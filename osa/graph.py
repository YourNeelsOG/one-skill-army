"""Ranking over the built graph: which nodes matter most.

Pure standard library, no numpy. Importance is approximated by degree (the
number of edges touching a node), which is cheap and good enough to surface the
files and symbols a reader should see first. Entrypoints are detected by name.
"""
from pathlib import Path

# Filename stems that usually mark a program's entry surface.
ENTRYPOINT_STEMS = {"main", "index", "cli", "app", "server", "__main__",
                    "__init__"}


def degree(graph):
    "Return {node_id: number of edges touching it} for every node."
    counts = {n["id"]: 0 for n in graph["nodes"]}
    for edge in graph["edges"]:
        for end in ("source", "target"):
            nid = edge.get(end)
            if nid in counts:
                counts[nid] += 1
    return counts


def god_nodes(graph, limit=20):
    "Return the most-connected node ids, highest degree first."
    d = degree(graph)
    ranked = sorted(d, key=lambda nid: (-d[nid], nid))
    return ranked[:limit]


def entrypoints(graph):
    "Return file node ids whose filename stem looks like an entry point."
    out = []
    for node in graph["nodes"]:
        if node.get("kind") != "file":
            continue
        if Path(node["id"]).stem.lower() in ENTRYPOINT_STEMS:
            out.append(node["id"])
    return out
