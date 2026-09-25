"""Generic regex extractor driven by one language table (see tables.py).

Pipeline for one file:
1. Scrub comments and string contents (scrub.py) so regexes only see code.
2. Find definitions. For each, find its body: the first "{" after the match
   (unless a ";" comes first) up to the matching "}". Brace counting is
   reliable because strings and comments are already blanked.
3. Nest definitions by body span. A function inside a class-like body becomes
   a method (`Class.method`, `method_of` edge); member-only patterns (class
   method syntax) are dropped outside a class, so `if (x) {` never becomes a
   symbol.
4. Emit imports, inheritance and references. Edges the file proves alone are
   EXTRACTED; cross-file targets are pending edges for osa/resolve.py.
"""
import bisect
import re

from .scrub import scrub

# Definitions whose body holds methods.
CLASS_LIKE = {"class", "interface", "struct", "trait", "impl", "enum",
              "record"}
# Control-flow words that member patterns can mistake for method names.
KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "new", "else",
            "do", "try", "finally", "with", "function", "typeof", "await",
            "super", "this", "synchronized", "throw", "case", "yield"}

# A string literal in scrubbed text: its contents are spaces, so no quotes.
STR = r"""(["'`][^"'`\n]*["'`])"""


def _body_end(text, start):
    "Return the index after the '}' closing the body that opens at/after start."
    n = len(text)
    i = start
    while i < n and text[i] not in "{;":
        i += 1
    if i >= n or text[i] == ";":
        return None
    depth = 0
    while i < n:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def _literal(source, match, group):
    "Read a matched group back from the original source, quotes stripped."
    start, end = match.span(group)
    return source[start:end].strip("\"'` \t")


def _base_names(raw):
    "Split an extends/implements list into bare type names."
    raw = re.sub(r"<[^<>]*>", "", raw)  # drop simple generic arguments
    out = []
    for part in raw.split(","):
        part = part.strip().lstrip("*&")
        if not part:
            continue
        name = re.split(r"::|\.", part)[-1].split()[0]
        if re.match(r"^\w+$", name):
            out.append(name)
    return out


def extract_with(table, path, source):
    "Return {'nodes', 'edges'} for one file using one language table."
    lang = table["lang"]
    flags = re.MULTILINE | (re.IGNORECASE if table.get("icase") else 0)
    text = scrub(source, table.get("line", ()), table.get("block", ()),
                 table.get("strings", ()), table.get("raw", ()))
    line_starts = [0] + [i + 1 for i, ch in enumerate(text) if ch == "\n"]

    def line_of(pos):
        return bisect.bisect_right(line_starts, pos)

    norm = table.get("normalize", lambda name: name)
    nodes = [{"id": path, "kind": "file", "name": path, "path": path,
              "line": 1, "lang": lang}]
    edges = []

    found = []  # (start, body_end, name, kind, member, explicit_parent)
    for spec in table.get("defines", ()):
        for m in re.finditer(spec["re"], text, flags):
            name = norm(m.group("name"))
            if spec.get("member") and name in KEYWORDS:
                continue
            parent = m.groupdict().get("parent")
            # Search for the body from the name: member regexes already
            # consume the opening "{", so m.end() would skip past it.
            body = _body_end(text, m.end("name"))
            found.append((m.start("name"), body, name, spec["kind"],
                          spec.get("member", False), parent))
    found.sort(key=lambda d: d[0])

    local = {}      # top-level name -> id, for same-file resolution
    ids = set()
    # Enclosing definitions: (body_end, qual, kind, node id or None). An impl
    # block has no node of its own: its methods point at the type by name.
    stack = []
    for start, end, name, kind, member, parent in found:
        while stack and stack[-1][0] <= start:
            stack.pop()
        encl = stack[-1] if stack else None
        in_class = encl is not None and encl[2] in CLASS_LIKE
        if member and not in_class:
            continue
        if kind == "impl":
            if end is not None:
                stack.append((end, name, "impl", None))
            continue
        owner = None  # node id, or a type name to resolve later
        if in_class and kind == "function":
            qual, kind = encl[1] + "." + name, "method"
            owner = encl[3] or encl[1]
        elif parent:
            qual, kind = norm(parent) + "." + name, "method"
            owner = norm(parent)
        else:
            qual = name
        nid = path + "::" + qual
        if end is not None:
            stack.append((end, qual, kind, nid))
        if nid in ids:
            continue
        ids.add(nid)
        nodes.append({"id": nid, "kind": kind, "name": name, "path": path,
                      "line": line_of(start), "lang": lang})
        if owner:
            edges.append({"source": nid, "rel": "method_of",
                          "line": line_of(start), "owner": owner})
        else:
            local.setdefault(name, nid)
            edges.append({"source": path, "target": nid, "rel": "defines",
                          "confidence": "EXTRACTED"})

    def to_symbol(name):
        "Final same-file target id, or a pending lookup by unique name."
        if name in local:
            return local[name]
        return {"name": name, "langs": table.get("family", [lang])}

    def add(source, rel, target, line):
        if target is None or target == source:
            return
        if isinstance(target, dict):
            edges.append({"source": source, "rel": rel, "line": line,
                          "resolve": target})
        else:
            edges.append({"source": source, "target": target, "rel": rel,
                          "confidence": "EXTRACTED", "line": line})

    # method_of edges were held until every same-file name was known.
    for e in edges:
        if e.get("rel") == "method_of" and "owner" in e:
            owner = e.pop("owner")
            target = owner if owner.startswith(path + "::") \
                else to_symbol(owner)
            if isinstance(target, dict):
                e["resolve"] = target
            else:
                e["target"], e["confidence"] = target, "EXTRACTED"

    resolve_import = table.get("resolve_import")
    for entry in table.get("imports", ()):
        # An entry is a regex, or (regex, resolver) when one language has
        # import forms that resolve differently (Rust `use` vs `mod x;`).
        pattern, resolver = entry if isinstance(entry, tuple) \
            else (entry, resolve_import)
        for m in re.finditer(pattern, text, flags):
            spec = resolver(path, _literal(source, m, 1))
            add(path, "imports", spec, line_of(m.start(1)))
    for pattern in table.get("import_blocks", ()):
        for block in re.finditer(pattern, text, flags):
            for m in re.finditer(STR, block.group(1)):
                pos = block.start(1) + m.start(1)
                lit = source[pos:pos + len(m.group(1))].strip("\"'`")
                add(path, "imports", resolve_import(path, lit), line_of(pos))

    for pattern in table.get("inherits", ()):
        for m in re.finditer(pattern, text, flags):
            sub = local.get(norm(m.group("sub")))
            if sub is None:
                continue
            for base in _base_names(m.group("base")):
                add(sub, "inherits", to_symbol(norm(base)), line_of(m.start()))
    for block_re, line_re in table.get("inherit_blocks", ()):
        for block in re.finditer(block_re, text, flags):
            sub = local.get(norm(block.group("sub")))
            if sub is None:
                continue
            for m in re.finditer(line_re, block.group("body"), re.MULTILINE):
                for base in _base_names(m.group("base")):
                    add(sub, "inherits", to_symbol(norm(base)),
                        line_of(block.start("body") + m.start()))

    # References: with from_symbol, the source is the innermost definition
    # whose body (or, with no body, whose statement up to the next ";")
    # holds the match. Otherwise, and outside any definition, the file.
    scopes = []
    for start, end, name, _, _, _ in found:
        if name in local:
            stop = end if end is not None else text.find(";", start)
            scopes.append((start, len(text) if stop < 0 else stop,
                           local[name]))
    for ref in table.get("references", ()):
        for m in re.finditer(ref["re"], text, flags):
            pos = m.start("ref")
            source_id = path
            if ref.get("from_symbol"):
                for start, stop, nid in scopes:
                    if start <= pos < stop:
                        source_id = nid
            raw = _literal(source, m, "ref")
            if ref["to"] == "symbol":
                target = to_symbol(norm(raw))
            else:
                target = ref["to"](path, raw)
            add(source_id, "references", target, line_of(pos))

    return {"nodes": nodes, "edges": edges}
