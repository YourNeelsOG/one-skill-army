"""Build the project graph by extracting every indexable file and merging.

Walks the project once, dispatches each file to its extractor, and merges the
fragments into a single graph. Nodes are de-duplicated by id so a module
imported from many files appears once; edges are kept as emitted.
"""
from .extractors import extract_file
from .scan import scan


def build_graph(root):
    "Return {'nodes': [...], 'edges': [...]} for the whole project at root."
    nodes = {}
    edges = []
    for rel, path in scan(root):
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            fragment = extract_file(rel, source)
        except SyntaxError:
            # A source file the parser cannot read still belongs in the graph
            # as a plain file node; never drop it silently.
            fragment = {"nodes": [{"id": rel, "kind": "file", "name": rel,
                                   "path": rel, "line": 1, "lang": "generic"}],
                        "edges": []}
        for node in fragment["nodes"]:
            nodes.setdefault(node["id"], node)
        edges.extend(fragment["edges"])

    _resolve_internal_imports(nodes, edges)
    return {"nodes": list(nodes.values()), "edges": edges}


def _resolve_internal_imports(nodes, edges):
    """Rewrite imports edges whose target is a UNIQUE local file stem.

    Conservative on purpose: a module name matching exactly one local file is
    rewritten to that file node; an ambiguous stem is left as-is rather than
    guessing, so no phantom edge is ever created.
    """
    from collections import Counter
    from pathlib import Path

    file_ids = [nid for nid, n in nodes.items() if n.get("kind") == "file"]
    stem_counts = Counter(Path(fid).stem for fid in file_ids)
    stem_to_file = {}
    for fid in file_ids:
        stem = Path(fid).stem
        if stem_counts[stem] == 1:
            stem_to_file[stem] = fid

    for edge in edges:
        if edge.get("rel") != "imports":
            continue
        target = edge.get("target")
        if target in nodes and nodes[target].get("kind") == "file":
            continue  # already a file
        resolved = stem_to_file.get(target)
        if resolved and resolved != edge.get("source"):
            edge["target"] = resolved
