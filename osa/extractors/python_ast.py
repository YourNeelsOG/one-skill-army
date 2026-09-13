"""Deterministic structural extractor for Python source files.

Uses the standard library `ast` module. No external dependencies. Given one
file's path and source text, returns the nodes and edges that describe the
file's structure: the file itself, the symbols it defines, and the modules it
imports. The engine never invents edges, so only relationships the parser can
see from the syntax tree are emitted.
"""
import ast


def extract(path, source):
    "Return {'nodes': [...], 'edges': [...]} for one Python source file."
    nodes = [{"id": path, "kind": "file", "name": path, "path": path,
              "line": 1, "lang": "python"}]
    edges = []
    seen_modules = set()
    tree = ast.parse(source)

    def add_symbol(name, kind, line):
        "Record a defined symbol node plus the file's defines edge to it."
        sid = path + "::" + name
        nodes.append({"id": sid, "kind": kind, "name": name, "path": path,
                      "line": line, "lang": "python"})
        edges.append({"source": path, "target": sid, "rel": "defines"})

    def add_import(module, line):
        "Record a module node (once) plus the file's imports edge to it."
        if module and module not in seen_modules:
            seen_modules.add(module)
            nodes.append({"id": module, "kind": "module", "name": module,
                          "path": path, "line": line, "lang": "python"})
        if module:
            edges.append({"source": path, "target": module, "rel": "imports"})

    defined = set()  # symbol names defined in this file, for calls resolution
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            add_symbol(node.name, "function", node.lineno)
            defined.add(node.name)
        elif isinstance(node, ast.ClassDef):
            add_symbol(node.name, "class", node.lineno)
            defined.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                # Top-level package only, so submodule imports collapse to one node.
                add_import(alias.name.split(".")[0], node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                add_import(node.module.split(".")[0], node.lineno)

    # Second pass: calls between symbols defined in THIS file only. A call to a
    # name not defined here is left out rather than invented as a phantom edge.
    seen_calls = set()
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        caller = path + "::" + func.name
        for inner in ast.walk(func):
            if not isinstance(inner, ast.Call):
                continue
            callee_name = None
            if isinstance(inner.func, ast.Name):
                callee_name = inner.func.id
            if callee_name and callee_name in defined and callee_name != func.name:
                callee = path + "::" + callee_name
                key = (caller, callee)
                if key not in seen_calls:
                    seen_calls.add(key)
                    edges.append({"source": caller, "target": callee,
                                  "rel": "calls"})

    return {"nodes": nodes, "edges": edges}
