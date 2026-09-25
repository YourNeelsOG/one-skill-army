"""Build the project graph by extracting every indexable file and merging.

Walks the project once, dispatches each file to its extractor, and merges the
fragments into a single graph. Nodes are de-duplicated by id so a module
imported from many files appears once. Pending cross-file edges are resolved
by osa/resolve.py, then hand-written manual edges are merged in.
"""
import hashlib
import json
from pathlib import Path

from .extractors import extract_file
from .resolve import resolve_edges
from .scan import scan

# Version of the graph.json layout. 2 added edge confidence and reasons.
SCHEMA = 2

# Closed set of relations an extractor may emit. Manual edges (written by hand
# with evidence) are the one source allowed to use other relation names.
RELATIONS = {"defines", "contains", "imports", "calls", "inherits",
             "method_of", "links_to", "references"}


def _extract(rel, source):
    "Return (fragment, error name or None) for one file's text."
    try:
        return extract_file(rel, source), None
    except (SyntaxError, ValueError, RecursionError) as exc:
        # A file the parser cannot read still belongs in the graph as a plain
        # file node, and the failure is recorded, never silent.
        return {"nodes": [{"id": rel, "kind": "file", "name": rel,
                           "path": rel, "line": 1, "lang": "generic"}],
                "edges": []}, type(exc).__name__


def build_graph(root, cache=None):
    """Return {'schema', 'nodes', 'edges', 'errors'} for the project at root.

    `cache` is an optional {rel_path: {"sha256", "fragment", "error"}} dict
    from a previous run. A file whose hash is unchanged reuses its cached
    fragment instead of being parsed again; cross-file resolution always runs
    over the whole graph, so the result equals a full build. On return the
    dict holds entries for exactly the current files.
    """
    nodes = {}
    edges = []
    errors = []  # files an extractor could not parse: {"path", "error"}
    current = {}
    for rel, path in scan(root):
        try:
            data = path.read_bytes()
        except OSError:
            continue
        digest = hashlib.sha256(data).hexdigest()
        hit = cache.get(rel) if cache else None
        if hit and hit.get("sha256") == digest:
            fragment, error = hit["fragment"], hit.get("error")
        else:
            try:
                source = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
            fragment, error = _extract(rel, source)
        current[rel] = {"sha256": digest, "fragment": fragment,
                        "error": error}
        if error:
            errors.append({"path": rel, "error": error})
        for node in fragment["nodes"]:
            nodes.setdefault(node["id"], node)
        edges.extend(fragment["edges"])

    if cache is not None:
        cache.clear()
        cache.update(current)
    edges = resolve_edges(nodes, edges)
    edges.extend(_manual_edges(root, nodes))
    return {"schema": SCHEMA, "nodes": list(nodes.values()), "edges": edges,
            "errors": errors}


def _manual_edges(root, nodes):
    """Load hand-written edges from .osa/graph/edges.jsonl as INFERRED edges.

    Each line is {"from", "rel", "to", "evidence", ...}. The evidence becomes
    the edge's reason. Lines that are not JSON, or that point at a node the
    graph does not have (a renamed or deleted file), are skipped so stale notes
    never create phantom edges.
    """
    path = Path(root) / ".osa" / "graph" / "edges.jsonl"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    out = []
    for line in lines:
        try:
            raw = json.loads(line)
        except ValueError:
            continue
        if not isinstance(raw, dict):
            continue
        source, target = raw.get("from"), raw.get("to")
        if source not in nodes or target not in nodes or not raw.get("rel"):
            continue
        out.append({"source": source, "target": target, "rel": raw["rel"],
                    "confidence": "INFERRED",
                    "reason": raw.get("evidence") or "manual edge",
                    "origin": "manual"})
    return out
