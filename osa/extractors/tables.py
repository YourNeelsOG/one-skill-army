"""Language tables for the regex extractor (table_extractor.py).

Each table is plain data plus, where a language needs it, one small function
that turns an import string into a resolve dict for osa/resolve.py. Adding a
language means adding one table here and one test file; the engine is shared.

Keys: lang, family (languages whose symbols may resolve each other by name),
ext, line/block/strings/raw (scrubber syntax), defines (regex with a `name`
group, a node kind, optional `member` and `parent` group), imports (regex whose
group 1 is the import text), import_blocks, inherits (`sub` and `base`
groups), inherit_blocks, references, icase, normalize, resolve_import.
"""
import posixpath

from .table_extractor import STR

C_COMMENTS = {"line": ["//"], "block": [("/*", "*/")]}


def _rel_join(path, spec):
    "Join an import path to the importing file's dir; None if it leaves root."
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(path), spec))
    return None if joined.startswith("..") else joined


JS_EXTS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".d.ts"]


def js_import(path, spec):
    "Relative specifiers probe extensions and index files; bare ones are packages."
    if spec.startswith("."):
        base = _rel_join(path, spec)
        if base is None:
            return None
        return {"files": [base] + [base + e for e in JS_EXTS]
                + [base + "/index" + e for e in JS_EXTS]}
    if not spec or spec.startswith("/"):
        return None
    parts = spec.split("/")
    package = "/".join(parts[:2]) if spec.startswith("@") else parts[0]
    return {"module": package}


_JS_MODS = r"(?:(?:export|default|declare|abstract|async)\s+)*"
JS = {
    "lang": "javascript",
    "family": ["javascript", "typescript"],
    "ext": [".js", ".jsx", ".mjs", ".cjs"],
    **C_COMMENTS,
    "strings": ['"', "'", "`"],
    "defines": [
        {"re": r"^\s*" + _JS_MODS + r"function\s*\*?\s*(?P<name>\w+)",
         "kind": "function"},
        {"re": r"^\s*" + _JS_MODS + r"class\s+(?P<name>\w+)", "kind": "class"},
        {"re": r"^\s*(?:export\s+)?(?:const|let|var)\s+(?P<name>\w+)\s*"
               r"(?::[^=\n]+)?=\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*"
               r"(?::[^=\n]+)?=>", "kind": "function"},
        {"re": r"^\s*" + _JS_MODS + r"interface\s+(?P<name>\w+)",
         "kind": "interface"},
        {"re": r"^\s*" + _JS_MODS + r"type\s+(?P<name>\w+)\s*(?:<[^>]*>)?\s*=",
         "kind": "type"},
        {"re": r"^\s*" + _JS_MODS + r"(?:const\s+)?enum\s+(?P<name>\w+)",
         "kind": "enum"},
        # Class members: only kept inside a class body (see table_extractor).
        {"re": r"^\s*(?:(?:public|private|protected|static|async|readonly|"
               r"abstract|override|get|set)\s+)*\*?(?P<name>\w+)\s*"
               r"(?:<[^>]*>)?\s*\([^)]*\)\s*(?::\s*[^{;]+)?\{",
         "kind": "function", "member": True},
    ],
    "imports": [
        r"\bimport\s+(?:type\s+)?[\w*{}\s,$]+?\s+from\s+" + STR,
        r"\bimport\s+" + STR,
        r"\bexport\s+(?:type\s+)?(?:\*(?:\s+as\s+\w+)?|\{[^}]*\})\s+from\s+"
        + STR,
        r"\brequire\s*\(\s*" + STR + r"\s*\)",
        r"\bimport\s*\(\s*" + STR + r"\s*\)",
    ],
    "inherits": [
        r"\bclass\s+(?P<sub>\w+)(?:\s*<[^>{]*>)?\s+extends\s+"
        r"(?P<base>[\w.]+)",
        r"\bclass\s+(?P<sub>\w+)[^{]*?\bimplements\s+(?P<base>[\w.,\s<>]+?)"
        r"\s*\{",
        r"\binterface\s+(?P<sub>\w+)(?:\s*<[^>{]*>)?\s+extends\s+"
        r"(?P<base>[\w.,\s<>]+?)\s*\{",
    ],
    "resolve_import": js_import,
}
TS = dict(JS, lang="typescript", ext=[".ts", ".tsx", ".mts", ".cts"])


def go_import(path, spec):
    "Go imports name a package directory; resolve.py matches it by path suffix."
    return {"package": spec, "package_ext": ".go", "module": spec}


GO = {
    "lang": "go",
    "ext": [".go"],
    **C_COMMENTS,
    "strings": ['"', "`", "'"],
    "raw": ["`"],
    "defines": [
        {"re": r"^func\s+\(\s*(?:\w+\s+)?\*?(?P<parent>\w+)(?:\[[^\]]*\])?\s*\)"
               r"\s*(?P<name>\w+)", "kind": "function"},
        {"re": r"^func\s+(?P<name>\w+)", "kind": "function"},
        {"re": r"^type\s+(?P<name>\w+)(?:\[[^\]]*\])?\s+struct\b",
         "kind": "struct"},
        {"re": r"^type\s+(?P<name>\w+)(?:\[[^\]]*\])?\s+interface\b",
         "kind": "interface"},
        {"re": r"^type\s+(?P<name>\w+)(?:\[[^\]]*\])?\s+(?!struct\b|interface\b)"
               r"[\w*\[\]]", "kind": "type"},
    ],
    "imports": [r"^\s*import\s+(?:[\w.]+\s+)?" + STR],
    "import_blocks": [r"^\s*import\s*\(([^)]*)\)"],
    # Embedded fields (a bare type name on its own line) are Go's inheritance.
    "inherit_blocks": [(r"^type\s+(?P<sub>\w+)\s+struct\s*\{(?P<body>[^}]*)\}",
                        r"^[ \t]*\*?(?P<base>[\w.]+)[ \t]*(?:`[^`]*`)?[ \t]*$")],
    "resolve_import": go_import,
}


def _rust_self_dir(path):
    "Directory holding this Rust module's children (2018 module layout)."
    stem = posixpath.splitext(posixpath.basename(path))[0]
    d = posixpath.dirname(path)
    if stem in ("main", "lib", "mod"):
        return d
    return posixpath.join(d, stem) if d else stem


def rust_mod(path, name):
    "`mod x;` loads x.rs or x/mod.rs next to this module: a syntax fact."
    d = _rust_self_dir(path)
    base = posixpath.join(d, name) if d else name
    return {"files": [base + ".rs", base + "/mod.rs"]}


def rust_use(path, spec):
    "`use` paths: crate-relative by suffix, self/super by path, else a crate."
    segs = [s for s in spec.split("::") if s]
    if not segs:
        return None
    head, rest = segs[0], segs[1:]
    if head in ("self", "super"):
        d = _rust_self_dir(path)
        if head == "super":
            d = posixpath.dirname(d)
        out = []
        for k in range(len(rest), 0, -1):
            base = posixpath.join(d, *rest[:k]) if d else "/".join(rest[:k])
            out += [base + ".rs", base + "/mod.rs"]
        return {"files": out} if out else None
    if head == "crate":
        suffixes = []
        for k in range(len(rest), 0, -1):
            p = "/".join(rest[:k])
            suffixes += ["src/" + p + ".rs", "src/" + p + "/mod.rs"]
        return {"suffixes": suffixes} if suffixes else None
    return {"module": head}


_RS_VIS = r"^\s*(?:pub(?:\([^)]*\))?\s+)?"
RUST = {
    "lang": "rust",
    "ext": [".rs"],
    **C_COMMENTS,
    "strings": ['"'],  # never "'": lifetimes like 'a would open a string
    "defines": [
        {"re": _RS_VIS + r"(?:(?:const|async|unsafe|extern)\s+)*fn\s+"
               r"(?P<name>\w+)", "kind": "function"},
        {"re": _RS_VIS + r"struct\s+(?P<name>\w+)", "kind": "struct"},
        {"re": _RS_VIS + r"enum\s+(?P<name>\w+)", "kind": "enum"},
        {"re": _RS_VIS + r"(?:unsafe\s+)?trait\s+(?P<name>\w+)",
         "kind": "trait"},
        {"re": _RS_VIS + r"type\s+(?P<name>\w+)", "kind": "type"},
        {"re": r"^\s*(?:unsafe\s+)?impl(?:<[^>]*>)?\s+(?:[\w:]+(?:<[^>]*>)?"
               r"\s+for\s+)?(?P<name>\w+)", "kind": "impl"},
    ],
    "imports": [
        (_RS_VIS + r"use\s+([\w:]+)", rust_use),
        (_RS_VIS + r"mod\s+(\w+)\s*;", rust_mod),
    ],
    "inherits": [r"^\s*(?:unsafe\s+)?impl(?:<[^>]*>)?\s+(?P<base>[\w:]+)"
                 r"(?:<[^>]*>)?\s+for\s+(?P<sub>\w+)"],
}


def java_import(path, spec):
    "Class imports match a file by package path suffix; else the package."
    static = spec.startswith("static")
    spec = spec[len("static"):].strip() if static else spec
    segs = spec.split(".")
    if static:
        segs = segs[:-1]  # drop the imported member, keep its class
    if segs and segs[-1] == "*":
        return {"module": ".".join(segs[:-1])}
    if len(segs) < 2:
        return None
    return {"suffixes": ["/".join(segs) + ".java"],
            "module": ".".join(segs[:-1])}


_JAVA_MODS = (r"^\s*(?:(?:public|private|protected|static|final|abstract|"
              r"sealed|non-sealed|strictfp)\s+)*")
JAVA = {
    "lang": "java",
    "ext": [".java"],
    **C_COMMENTS,
    "strings": ['"', "'"],
    "defines": [
        {"re": _JAVA_MODS + r"class\s+(?P<name>\w+)", "kind": "class"},
        {"re": _JAVA_MODS + r"interface\s+(?P<name>\w+)", "kind": "interface"},
        {"re": _JAVA_MODS + r"enum\s+(?P<name>\w+)", "kind": "enum"},
        {"re": _JAVA_MODS + r"record\s+(?P<name>\w+)", "kind": "record"},
        {"re": r"^\s*(?:(?:public|private|protected|static|final|abstract|"
               r"synchronized|native|default|strictfp)\s+)*(?:<[^>]+>\s+)?"
               r"(?:[\w<>\[\],.?]+[ \t]+)?(?P<name>\w+)\s*\([^)]*\)\s*"
               r"(?:throws\s+[\w.,\s]+)?\{", "kind": "function", "member": True},
    ],
    "imports": [r"^\s*import\s+((?:static\s+)?[\w.*]+)\s*;"],
    "inherits": [
        r"\bclass\s+(?P<sub>\w+)(?:<[^>{]*>)?\s+extends\s+(?P<base>[\w.]+)",
        r"\b(?:class|record|enum)\s+(?P<sub>\w+)[^{]*?\bimplements\s+"
        r"(?P<base>[\w.,\s<>]+?)\s*\{",
        r"\binterface\s+(?P<sub>\w+)(?:<[^>{]*>)?\s+extends\s+"
        r"(?P<base>[\w.,\s<>]+?)\s*\{",
    ],
    "resolve_import": java_import,
}



def _sql_name(raw):
    "Unquote and drop the schema: `\"public\".\"Users\"` becomes `users`."
    return raw.split(".")[-1].strip('"`[]').lower()


_SQL_NAME = r"(?P<name>[\w.\"`\[\]]+)"
_SQL_REF = r"(?P<ref>[\w.\"`\[\]]+)"
_SQL_CREATE = r"\bCREATE\s+(?:OR\s+REPLACE\s+)?"
_SQL_IFNE = r"(?:IF\s+NOT\s+EXISTS\s+)?"
SQL = {
    "lang": "sql",
    "ext": [".sql"],
    "icase": True,
    "normalize": _sql_name,
    "line": ["--"],
    "block": [("/*", "*/")],
    "strings": ["'"],  # double quotes are identifiers in SQL, not strings
    "defines": [
        {"re": _SQL_CREATE + r"(?:(?:TEMP|TEMPORARY|UNLOGGED|GLOBAL|LOCAL)"
               r"\s+)*TABLE\s+" + _SQL_IFNE + _SQL_NAME, "kind": "table"},
        {"re": _SQL_CREATE + r"(?:MATERIALIZED\s+)?VIEW\s+" + _SQL_IFNE
               + _SQL_NAME, "kind": "view"},
        {"re": _SQL_CREATE + r"FUNCTION\s+" + _SQL_NAME, "kind": "function"},
        {"re": _SQL_CREATE + r"PROCEDURE\s+" + _SQL_NAME,
         "kind": "procedure"},
        {"re": r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?"
               + _SQL_IFNE + _SQL_NAME, "kind": "index"},
    ],
    "references": [
        {"re": r"\bREFERENCES\s+" + _SQL_REF, "to": "symbol",
         "from_symbol": True},
        {"re": r"\b(?:FROM|JOIN)\s+" + _SQL_REF, "to": "symbol",
         "from_symbol": True},
        {"re": r"\bINDEX\s+(?:CONCURRENTLY\s+)?" + _SQL_IFNE
               + r"[\w.\"`\[\]]+\s+ON\s+(?:ONLY\s+)?" + _SQL_REF,
         "to": "symbol", "from_symbol": True},
    ],
}


def path_suffixes(path, spec):
    """Match a path written in a script or config file by path suffix.

    Shell and config paths are relative to some working directory, not the
    file, and often start with a variable (`$DIR/lib.sh`), so a match is
    INFERRED: variable segments are dropped and the rest must match exactly
    one file's suffix.
    """
    segs = [s for s in spec.split("/") if s and s != "."
            and not any(c in s for c in "$`(){}")]
    if not segs or ".." in segs:
        return None
    return {"suffixes": ["/".join(segs[k:]) for k in range(len(segs))]}


SHELL = {
    "lang": "shell",
    "ext": [".sh", ".bash", ".zsh"],
    # Strings stay visible: shell paths are usually quoted ("$DIR/lib.sh").
    # A "#" inside a string only counts as a comment after whitespace.
    "line": ["#"],
    "defines": [
        {"re": r"^\s*(?:function\s+)?(?P<name>[\w.:-]+)\s*\(\s*\)",
         "kind": "function"},
        {"re": r"^\s*function\s+(?P<name>[\w.:-]+)", "kind": "function"},
    ],
    "imports": [(r"^\s*(?:source|\.)\s+(\S+)", path_suffixes)],
    "references": [
        {"re": r"(?P<ref>[\w.${}\"/-]*/[\w.-]+\.(?:sh|bash|zsh|py))\b",
         "to": path_suffixes},
    ],
}

TABLES = [JS, TS, GO, RUST, JAVA, SQL, SHELL]
