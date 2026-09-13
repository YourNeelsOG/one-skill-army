"""Fallback extractor for files with no language-specific parser.

Emits a single file node so the file still appears in the graph and can be a
target of import or reference edges, without claiming any internal structure.
"""


def extract(path, source):
    "Return a graph fragment with just the file node."
    return {
        "nodes": [{"id": path, "kind": "file", "name": path, "path": path,
                   "line": 1, "lang": "generic"}],
        "edges": [],
    }
