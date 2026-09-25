"""Deterministic structural extractor for Python source files.

Uses the standard library `ast` module. No external dependencies. Given one
file's path (relative to the project root) and source text, returns the file,
the symbols it defines (functions, classes, methods as `Class.method`), and
the edges between them.

Edges this file can prove on its own (defines, method_of, same-file calls and
inheritance) are final and EXTRACTED. Edges that point into another file
(imports, calls and base classes reached through an import) are emitted as
pending edges with a `resolve` dict; osa/resolve.py finishes them once every
file is known. See that module for the resolution rules.
"""
import ast
import builtins
import posixpath

_BUILTINS = set(dir(builtins))
_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _module_files(base):
    "Candidate files for a dotted module turned into a root-relative base path."
    if base is None:
        return []
    if not base:
        return ["__init__.py"]
    return [base + ".py", base + "/__init__.py"]


def _join(*parts):
    "Join posix path parts; return None if the result escapes the root."
    parts = [p for p in parts if p]
    if not parts:
        return ""
    joined = posixpath.normpath(posixpath.join(*parts))
    if joined == ".":
        return ""
    if joined.startswith(".."):
        return None
    return joined


def _import_base(path, module, level):
    "Return the root-relative base path for `from <level dots><module>`."
    dotted = module.replace(".", "/") if module else ""
    if level == 0:
        return dotted
    pkg = posixpath.dirname(path)
    for _ in range(level - 1):
        pkg = posixpath.dirname(pkg) if pkg else None
        if pkg is None:
            return None
    return _join(pkg, dotted)


def extract(path, source):
    "Return {'nodes': [...], 'edges': [...]} for one Python source file."
    tree = ast.parse(source)
    nodes = [{"id": path, "kind": "file", "name": path, "path": path,
              "line": 1, "lang": "python"}]
    edges = []
    local = set()       # qualified names defined in this file ("f", "A", "A.m")
    bindings = {}       # imported name -> {"module": [files], "sub": [files]}
    functions = []      # (qualname, class name or None, def node)
    classes = []        # (qualname, class node)

    def sid(qual):
        return path + "::" + qual

    def add_symbol(qual, kind, line):
        nodes.append({"id": sid(qual), "kind": kind, "name": qual.split(".")[-1],
                      "path": path, "line": line, "lang": "python"})
        local.add(qual)

    def visit(body, cls):
        "Record definitions in module or class body; nested defs are skipped."
        for node in body:
            if isinstance(node, _DEFS):
                qual = cls + "." + node.name if cls else node.name
                add_symbol(qual, "method" if cls else "function", node.lineno)
                functions.append((qual, cls, node))
                if cls:
                    edges.append({"source": sid(qual), "target": sid(cls),
                                  "rel": "method_of", "confidence": "EXTRACTED"})
                else:
                    edges.append({"source": path, "target": sid(qual),
                                  "rel": "defines", "confidence": "EXTRACTED"})
            elif isinstance(node, ast.ClassDef):
                qual = cls + "." + node.name if cls else node.name
                add_symbol(qual, "class", node.lineno)
                classes.append((qual, node))
                parent = sid(cls) if cls else path
                edges.append({"source": parent, "target": sid(qual),
                              "rel": "defines", "confidence": "EXTRACTED"})
                visit(node.body, qual)

    def add_import(files, module, line):
        "Pending imports edge: local file first, else external package node."
        top = module.split(".")[0] if module else None
        stem = module.split(".")[-1] if module else None
        edges.append({"source": path, "rel": "imports", "line": line,
                      "resolve": {"files": files, "module": top,
                                  "stem": stem}})

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                files = _module_files(alias.name.replace(".", "/"))
                add_import(files, alias.name, node.lineno)
                if alias.asname or "." not in alias.name:
                    bindings[alias.asname or alias.name] = {"module": files,
                                                            "sub": []}
        elif isinstance(node, ast.ImportFrom):
            base = _import_base(path, node.module, node.level)
            if base is None:
                continue
            mod_files = _module_files(base)
            # Relative imports are local by definition: no external fallback.
            external = node.module if node.level == 0 else None
            for alias in node.names:
                if alias.name == "*":
                    add_import(mod_files, external, node.lineno)
                    continue
                sub = _module_files(_join(base, alias.name))
                add_import(sub + mod_files, external, node.lineno)
                bindings[alias.asname or alias.name] = {"module": mod_files,
                                                        "sub": sub}

    visit(tree.body, None)

    def target_for(expr, cls, skip=()):
        """Return a final target id, a pending resolve dict, or None.

        `expr` is the callee of a call or a base class expression. `skip` holds
        names that are local variables or parameters, never symbols.
        """
        if isinstance(expr, ast.Name):
            name = expr.id
            if name in skip:
                return None
            if name in local:
                return sid(name)
            if name in bindings:
                return {"files": bindings[name]["module"], "symbol": name}
            if name in _BUILTINS:
                return None
            return {"name": name, "langs": ["python"]}
        if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
            owner, attr = expr.value.id, expr.attr
            if owner in ("self", "cls") and cls:
                qual = cls + "." + attr
                return sid(qual) if qual in local else None
            if owner in local and owner + "." + attr in local:
                return sid(owner + "." + attr)
            if owner in bindings:
                b = bindings[owner]
                return {"files": b["sub"] or b["module"], "symbol": attr}
        return None

    def add_edge(source, rel, target, line):
        if target is None or target == source:
            return
        if isinstance(target, dict):
            edges.append({"source": source, "rel": rel, "line": line,
                          "resolve": target})
        else:
            edges.append({"source": source, "target": target, "rel": rel,
                          "confidence": "EXTRACTED", "line": line})

    for qual, node in classes:
        for base in node.bases:
            add_edge(sid(qual), "inherits", target_for(base, None),
                     node.lineno)

    for qual, cls, func in functions:
        args = func.args
        params = {a.arg for a in args.args + args.kwonlyargs
                  + getattr(args, "posonlyargs", [])}
        params.update(a.arg for a in (args.vararg, args.kwarg) if a)
        assigned = {t.id for t in ast.walk(func)
                    if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store)}
        for inner in ast.walk(func):
            if isinstance(inner, ast.Call):
                add_edge(sid(qual), "calls",
                         target_for(inner.func, cls, params | assigned),
                         inner.lineno)

    return {"nodes": nodes, "edges": edges}
