"""Turn the built graph into the smallest useful context for an LLM.

`build_context` writes the project map an agent reads first: entrypoints, the
most-connected nodes, a per-directory tally, and a symbol index, trimmed to a
token budget so it stays cheap. `context_slice` answers a specific question by
returning only the matching nodes and their immediate neighbors, so the agent
never has to scan the whole repository to find where something lives.
"""
from collections import Counter
from pathlib import Path

from .analyze import (communities, god_nodes_by_betweenness,
                      suggested_questions, surprising_connections)
from .graph import degree, entrypoints, god_nodes

# Betweenness is O(V*E); skip the heavy analysis above this many nodes.
_ANALYSIS_NODE_CAP = 3000


def _neighbors(graph, node_id):
    "Return ids directly connected to node_id by any edge."
    out = set()
    for edge in graph["edges"]:
        if edge.get("source") == node_id:
            out.add(edge.get("target"))
        elif edge.get("target") == node_id:
            out.add(edge.get("source"))
    out.discard(None)
    return out


def build_context(graph, budget=1500):
    "Return a markdown project digest trimmed to `budget` characters."
    eps = entrypoints(graph)
    gods = god_nodes(graph, limit=15)
    dirs = Counter()
    for node in graph["nodes"]:
        if node.get("kind") == "file":
            parent = str(Path(node["id"]).parent)
            dirs[parent] += 1

    lines = ["# Project map", ""]
    lines.append("## Entrypoints")
    lines.extend("- " + e for e in eps) if eps else lines.append("- (none detected)")

    # Deterministic analysis first (the high-value part); skip on huge graphs to
    # keep indexing fast. Directory listing goes last so truncation trims it, not
    # the insights.
    if len(graph["nodes"]) <= _ANALYSIS_NODE_CAP:
        comm = communities(graph)
        # Count clusters that hold more than one node; singleton leaf symbols
        # are not meaningful "clusters".
        sizes = Counter(comm.values())
        num_comm = sum(1 for c in sizes.values() if c > 1)
        lines.append("")
        lines.append("## Most central (bridges)")
        # Exclude external modules: an imported stdlib package is a hub but not
        # project structure the reader is looking for.
        for nid in god_nodes_by_betweenness(graph, limit=10,
                                            exclude_kinds=("module",)):
            lines.append("- " + nid)

        lines.append("")
        lines.append("## Communities")
        lines.append("- " + str(num_comm) + " clusters (2+ nodes) detected")

        surprises = surprising_connections(graph, comm)
        if surprises:
            lines.append("")
            lines.append("## Surprising connections")
            for s in surprises[:8]:
                lines.append("- " + s["source"] + " -> " + s["target"]
                             + " (" + s["rel"] + ")")

        questions = suggested_questions(graph, comm, limit=5,
                                        exclude_kinds=("module",))
        if questions:
            lines.append("")
            lines.append("## Questions this graph can answer")
            for q in questions:
                lines.append("- " + q)

    lines.append("")
    lines.append("## Most connected")
    lines.extend("- " + g for g in gods)
    lines.append("")
    lines.append("## Directories")
    for name, count in dirs.most_common():
        lines.append("- " + name + " (" + str(count) + " files)")

    text = "\n".join(lines)
    if len(text) > budget:
        text = text[:budget]
    return text


def context_slice(graph, query, budget=1500):
    "Return a markdown slice: nodes matching `query` plus their neighbors."
    q = query.lower()
    matches = [n for n in graph["nodes"]
               if q in n["id"].lower() or q in n.get("name", "").lower()]
    if not matches:
        return "No match for '" + query + "' in the project graph."

    lines = ["# Context for '" + query + "'", ""]
    for node in matches[:20]:
        loc = ""
        if node.get("line"):
            loc = " (" + node["path"] + ":" + str(node["line"]) + ")" \
                if node.get("path") else ""
        lines.append("## " + node["id"] + loc)
        neigh = sorted(_neighbors(graph, node["id"]))
        for nb in neigh:
            lines.append("- " + nb)
        lines.append("")

    text = "\n".join(lines)
    if len(text) > budget:
        text = text[:budget]
    return text
