"""Write the full, untruncated graph report (.osa/GRAPH_REPORT.md).

context.md is the short map an agent reads every session; this report is the
long form a human (or an agent with a real question) reads on demand. It says
what the graph holds, how much of it is EXTRACTED versus INFERRED, which nodes
carry the structure, how the project clusters, and lists every inferred edge
with its reason so a reviewer can check the heuristics.
"""
from collections import Counter
from pathlib import PurePosixPath

from .analyze import (betweenness, communities, suggested_questions,
                      surprising_connections)
from .graph import degree, entrypoints

# Betweenness is O(V*E); above this many nodes the heavy sections are skipped.
ANALYSIS_NODE_CAP = 3000
# Long lists are capped so a huge project still yields a readable file.
LIST_CAP = 200


def _capped(items, render):
    "Render up to LIST_CAP items, then a line saying how many were left out."
    lines = [render(item) for item in items[:LIST_CAP]]
    if len(items) > LIST_CAP:
        lines.append("- ... " + str(len(items) - LIST_CAP) + " more")
    return lines or ["- (none)"]


def community_labels(graph, comm):
    """Return {community: label} as "<most common directory>/ (<hub name>)".

    Deterministic and model-free: the directory most members live in, plus
    the name of the best connected member.
    """
    deg = degree(graph)
    by_id = {n["id"]: n for n in graph["nodes"]}
    members = {}
    for nid, c in comm.items():
        members.setdefault(c, []).append(nid)
    labels = {}
    for c, ids in members.items():
        dirs = Counter(str(PurePosixPath(by_id[i].get("path") or i).parent)
                       for i in ids if i in by_id)
        top_dir = dirs.most_common(1)[0][0] if dirs else "."
        # The hub is a project node; an imported package is never the label.
        local = [i for i in ids if by_id.get(i, {}).get("kind") != "module"]
        hub = max(local or ids, key=lambda i: (deg.get(i, 0), i))
        name = by_id.get(hub, {}).get("name", hub)
        labels[c] = ("./" if top_dir == "." else top_dir + "/") \
            + " (" + str(name) + ")"
    return labels


def build_report(graph):
    "Return the GRAPH_REPORT.md text for a built graph."
    nodes, edges = graph["nodes"], graph["edges"]
    lines = ["# Graph report", "",
             "Every edge is EXTRACTED (read from syntax) or INFERRED "
             "(matched by a heuristic, reason given). Source of truth is "
             "the files; this is an index.", "", "## Summary", "",
             "- " + str(len(nodes)) + " nodes, " + str(len(edges)) + " edges",
             ""]
    kinds = Counter(n.get("kind", "?") for n in nodes)
    lines += ["| Node kind | Count |", "|---|---|"]
    lines += ["| " + k + " | " + str(v) + " |" for k, v in kinds.most_common()]
    rels = Counter((e["rel"], e.get("confidence", "?")) for e in edges)
    lines += ["", "| Relation | EXTRACTED | INFERRED |", "|---|---|---|"]
    for rel in sorted({r for r, _ in rels}):
        lines.append("| " + rel + " | " + str(rels[(rel, "EXTRACTED")])
                     + " | " + str(rels[(rel, "INFERRED")]) + " |")

    lines += ["", "## Entrypoints", ""]
    lines += _capped(entrypoints(graph), lambda e: "- " + e)

    deg = degree(graph)
    kind_of = {n["id"]: n.get("kind") for n in nodes}
    gods = sorted((n for n in deg if kind_of.get(n) != "module"),
                  key=lambda n: (-deg[n], n))[:20]
    lines += ["", "## God nodes", ""]
    lines += _capped(gods, lambda n: "- " + n + " (degree " + str(deg[n])
                     + ")")

    heavy = len(nodes) <= ANALYSIS_NODE_CAP
    lines += ["", "## Bridges", ""]
    comm = communities(graph) if heavy else {}
    if heavy:
        bc = betweenness(graph)
        bridges = sorted((n for n in bc if kind_of.get(n) != "module"
                          and bc[n] > 0), key=lambda n: (-bc[n], n))[:15]
        lines += _capped(bridges, lambda n: "- " + n + " (betweenness "
                         + format(bc[n], ".1f") + ")")
    else:
        lines.append("- (skipped: more than " + str(ANALYSIS_NODE_CAP)
                     + " nodes)")

    lines += ["", "## Communities", ""]
    if heavy:
        labels = community_labels(graph, comm)
        sizes = Counter(comm.values())
        groups = [c for c, size in sizes.most_common() if size > 1]

        def render(c):
            members = sorted((n for n in comm if comm[n] == c),
                             key=lambda n: (-deg.get(n, 0), n))[:5]
            return ("- **" + labels[c] + "**: " + str(sizes[c])
                    + " nodes; top: " + ", ".join(members))
        lines += _capped(groups, render)
    else:
        lines.append("- (skipped)")

    lines += ["", "## Surprising connections", ""]
    surprises = surprising_connections(graph, comm) if heavy else []
    lines += _capped(surprises, lambda s: "- " + s["source"] + " --"
                     + s["rel"] + "--> " + s["target"])

    inferred = [e for e in edges if e.get("confidence") == "INFERRED"]
    lines += ["", "## Inferred edges (review these)", ""]
    lines += _capped(inferred, lambda e: "- " + e["source"] + " --" + e["rel"]
                     + "--> " + e["target"] + " (" + e.get("reason", "?")
                     + ")")

    lines += ["", "## Index errors", ""]
    lines += _capped(graph.get("errors", []),
                     lambda e: "- " + e["path"] + ": " + e["error"])

    lines += ["", "## Questions", ""]
    questions = suggested_questions(graph, comm, limit=8,
                                    exclude_kinds=("module",)) if heavy else []
    lines += _capped(questions, lambda q: "- " + q)
    return "\n".join(lines) + "\n"
