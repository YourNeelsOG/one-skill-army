"""Deterministic graph analysis: centrality and community structure.

Pure standard library, no numpy, no LLM. These are the analyses a knowledge
graph needs to be useful (which nodes bridge the system, which clusters exist,
which connections are surprising) computed cheaply and reproducibly so the same
graph always yields the same answer.
"""
from collections import deque


def _node_labels(graph):
    "Return {node_id: human label} for summaries."
    return {n["id"]: n.get("name", n["id"]) for n in graph["nodes"]}


def adjacency(graph):
    "Return {node_id: sorted list of neighbor ids} for the undirected graph."
    adj = {n["id"]: set() for n in graph["nodes"]}
    for edge in graph["edges"]:
        s, t = edge.get("source"), edge.get("target")
        if s in adj and t in adj and s != t:
            adj[s].add(t)
            adj[t].add(s)
    return {nid: sorted(neigh) for nid, neigh in adj.items()}


def betweenness(graph):
    "Return {node_id: betweenness centrality} via Brandes (unweighted)."
    adj = adjacency(graph)
    bc = {nid: 0.0 for nid in adj}
    for source in sorted(adj):
        stack = []
        preds = {nid: [] for nid in adj}
        sigma = {nid: 0.0 for nid in adj}
        dist = {nid: -1 for nid in adj}
        sigma[source] = 1.0
        dist[source] = 0
        queue = deque([source])
        while queue:
            v = queue.popleft()
            stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    preds[w].append(v)
        delta = {nid: 0.0 for nid in adj}
        while stack:
            w = stack.pop()
            for v in preds[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != source:
                bc[w] += delta[w]
    # Undirected graph counts each shortest path from both ends.
    return {nid: score / 2.0 for nid, score in bc.items()}


def _kinds(graph):
    "Return {node_id: kind}."
    return {n["id"]: n.get("kind", "node") for n in graph["nodes"]}


def god_nodes_by_betweenness(graph, limit=20, exclude_kinds=()):
    "Return the highest-betweenness node ids, most central first."
    bc = betweenness(graph)
    if exclude_kinds:
        kinds = _kinds(graph)
        bc = {nid: v for nid, v in bc.items()
              if kinds.get(nid) not in exclude_kinds}
    ranked = sorted(bc, key=lambda nid: (-bc[nid], nid))
    return ranked[:limit]


def communities(graph):
    "Return {node_id: community_int} by deterministic modularity (Louvain move)."
    adj = adjacency(graph)
    order = sorted(adj)
    deg = {n: len(adj[n]) for n in order}
    m = sum(deg.values()) / 2.0
    comm = {n: i for i, n in enumerate(order)}
    if m == 0:
        return comm  # all isolated: each its own community
    tot = {i: deg[order[i]] for i in range(len(order))}  # sum degrees per comm

    improved = True
    while improved:
        improved = False
        for n in order:
            ci = comm[n]
            ki = deg[n]
            tot[ci] -= ki  # take n out of its community
            nb_comm = {ci: 0}
            for w in adj[n]:
                nb_comm[comm[w]] = nb_comm.get(comm[w], 0) + 1
            best_c, best_gain = ci, -1.0
            for c, kin in sorted(nb_comm.items()):
                gain = kin - tot.get(c, 0) * ki / (2.0 * m)
                if gain > best_gain + 1e-12:  # strict: smallest c wins ties
                    best_gain, best_c = gain, c
            comm[n] = best_c
            tot[best_c] = tot.get(best_c, 0) + ki
            if best_c != ci:
                improved = True

    remap = {}
    for n in order:
        if comm[n] not in remap:
            remap[comm[n]] = len(remap)
    return {n: remap[comm[n]] for n in order}


# Parent-child structure, never a "surprising" cross-cutting link.
STRUCTURAL_RELS = {"defines", "contains"}


def surprising_connections(graph, comm):
    "Return non-structural edges whose endpoints lie in different communities."
    out = []
    seen = set()
    for edge in graph["edges"]:
        s, t = edge.get("source"), edge.get("target")
        if s not in comm or t not in comm or s == t:
            continue
        if edge.get("rel") in STRUCTURAL_RELS:
            continue
        if comm[s] == comm[t]:
            continue
        key = tuple(sorted((s, t)))
        if key in seen:
            continue
        seen.add(key)
        out.append({"source": s, "target": t, "rel": edge.get("rel", "")})
    out.sort(key=lambda e: (e["source"], e["target"]))
    return out


def suggested_questions(graph, comm, limit=5, exclude_kinds=()):
    "Return questions about the highest-betweenness cross-community bridges."
    bc = betweenness(graph)
    adj = adjacency(graph)
    labels = _node_labels(graph)
    kinds = _kinds(graph)
    bridges = []
    for nid in adj:
        if kinds.get(nid) in exclude_kinds:
            continue
        neigh_comms = {comm[w] for w in adj[nid] if w in comm}
        neigh_comms.discard(comm.get(nid))
        if neigh_comms:
            bridges.append(nid)
    bridges.sort(key=lambda n: (-bc[n], n))
    questions = []
    for nid in bridges[:limit]:
        questions.append(
            "How does '" + labels[nid] + "' connect otherwise separate parts "
            "of the system? (betweenness " + format(bc[nid], ".2f") + ")")
    return questions


def shortest_path(graph, source, target):
    "Return the node ids on a shortest path source->target, or [] if none."
    adj = adjacency(graph)
    if source not in adj or target not in adj:
        return []
    if source == target:
        return [source]
    prev = {source: None}
    queue = deque([source])
    while queue:
        v = queue.popleft()
        if v == target:
            break
        for w in adj[v]:
            if w not in prev:
                prev[w] = v
                queue.append(w)
    if target not in prev:
        return []
    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def explain(graph, node_id):
    "Return a role summary for one node: degree, community, centrality, links."
    adj = adjacency(graph)
    if node_id not in adj:
        return {"id": node_id, "summary": "Node not in graph."}
    comm = communities(graph)
    bc = betweenness(graph)
    labels = _node_labels(graph)
    neighbors = adj[node_id]
    kind = next((n.get("kind") for n in graph["nodes"]
                 if n["id"] == node_id), "node")
    summary = (labels[node_id] + " is a " + str(kind) + " with "
               + str(len(neighbors)) + " connection(s), in community "
               + str(comm[node_id]) + ", betweenness "
               + format(bc[node_id], ".2f") + ".")
    return {
        "id": node_id,
        "kind": kind,
        "degree": len(neighbors),
        "community": comm[node_id],
        "betweenness": bc[node_id],
        "neighbors": neighbors,
        "summary": summary,
    }
