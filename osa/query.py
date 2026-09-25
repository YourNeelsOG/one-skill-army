"""Answer questions against the built graph without reading the repository.

- `resolve_node` turns what a user typed into one node id (or candidates).
- `query` scores nodes against a plain-language question, then walks out from
  the best matches and returns the connecting subgraph, trimmed to a token
  budget so the answer stays cheap to read.
- `affected` walks dependency edges backwards: who imports, calls, inherits
  or references this, directly or transitively.
- `describe` and `path_hops` give `explain` and `path` their relation-aware
  text: every edge is shown with its relation and EXTRACTED/INFERRED label.

All pure standard library and deterministic: same graph, same answer.
"""
import math
import re
from collections import defaultdict, deque

from .graph import degree
from .measure import CHARS_PER_TOKEN

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "get", "has", "have", "how", "i", "in", "into", "is", "it",
    "me", "of", "on", "or", "show", "that", "the", "this", "to", "use",
    "uses", "used", "what", "when", "where", "which", "who", "why", "with",
    "work", "works", "between", "about",
}
# Relations that mean "depends on": walked backwards by `affected`.
DEPENDENCY_RELS = ("imports", "calls", "inherits", "references", "links_to")
# Relations from a container to what it holds.
CHILD_RELS = ("defines", "contains")
MAX_SEEDS = 5
MAX_NODES = 80


def _words(text):
    "Split identifiers and prose into lowercase words (camel and snake case)."
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return [w.lower() for w in re.split(r"[^A-Za-z0-9]+", text) if w]


def tokenize(question):
    "Return search terms: whole identifiers plus their parts, no stopwords."
    terms = []
    for raw in re.findall(r"[A-Za-z0-9_]+", question):
        for term in [raw.lower()] + _words(raw):
            if len(term) > 1 and term not in STOPWORDS and term not in terms:
                terms.append(term)
    return terms


def resolve_node(graph, text):
    """Return (node_id, []) for one clear match, else (None, candidates).

    Tries, in order: exact id, exact name, case-insensitive name, then a
    case-insensitive substring of the id. Candidates (up to 10, most
    connected first) are returned only when the text is ambiguous.
    """
    nodes = graph["nodes"]
    ids = {n["id"] for n in nodes}
    if text in ids:
        return text, []
    low = text.lower()
    for pick in (lambda n: n.get("name") == text,
                 lambda n: str(n.get("name", "")).lower() == low,
                 lambda n: low in n["id"].lower()):
        hits = [n["id"] for n in nodes if pick(n)]
        if len(hits) == 1:
            return hits[0], []
        if hits:
            deg = degree(graph)
            hits.sort(key=lambda nid: (-deg.get(nid, 0), nid))
            return None, hits[:10]
    return None, []


def _adjacency(graph):
    "Return {node: [(neighbor, edge)]} over edges in both directions."
    adj = defaultdict(list)
    for edge in graph["edges"]:
        adj[edge["source"]].append((edge["target"], edge))
        adj[edge["target"]].append((edge["source"], edge))
    return adj


def _label(edge):
    return "[E]" if edge.get("confidence") == "EXTRACTED" else "[I]"


def _loc(node):
    return (node.get("path") or node["id"]) + ":" + str(node.get("line", 1))


def _trim(text, budget):
    "Cut text to `budget` tokens at a line boundary."
    limit = budget * CHARS_PER_TOKEN
    if len(text) <= limit:
        return text
    cut = text[:limit - 12].rsplit("\n", 1)[0]
    return cut + "\n(truncated)"


def stem(word):
    "Crude suffix strip so resolver/resolve and edges/edge meet."
    for suffix in ("ing", "ers", "er", "es", "ed", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[:-len(suffix)]
            break
    return word[:-1] if word.endswith("e") and len(word) > 3 else word


def score_nodes(graph, terms):
    """Return [(score, node_id)] best first.

    A term scores 3 for an exact name, 2 for a word in the name, 1 for a word
    in the path, each times the term's rarity (inverse document frequency),
    so a word shared by half the project counts for little. Ties go to the
    better connected node.
    """
    nodes = graph["nodes"]
    words = {}
    for node in nodes:
        name_stems = {stem(w) for w in _words(str(node.get("name", "")))}
        path_stems = {stem(w) for w in _words(node.get("path") or "")}
        words[node["id"]] = (name_stems, path_stems)
    weights = {}
    for term in terms:
        st = stem(term)
        df = sum(1 for name_s, path_s in words.values()
                 if st in name_s or st in path_s)
        if df:
            weights[term] = math.log((len(nodes) + 1) / (df + 1)) + 0.1
    deg = degree(graph)
    scored = []
    for node in nodes:
        name = str(node.get("name", "")).lower()
        name_s, path_s = words[node["id"]]
        score = 0.0
        for term, weight in weights.items():
            st = stem(term)
            if term == name:
                score += 3 * weight
            elif st in name_s:
                score += 2 * weight
            elif st in path_s:
                score += weight
        if score:
            scored.append((score, deg.get(node["id"], 0), node["id"]))
    scored.sort(key=lambda s: (-s[0], -s[1], s[2]))
    return [(s, nid) for s, _, nid in scored]


def query(graph, question, depth=2, budget=2000, dfs=False):
    "Return {'seeds', 'nodes', 'edges', 'text'} for a plain-language question."
    terms = tokenize(question)
    seeds = [nid for _, nid in score_nodes(graph, terms)[:MAX_SEEDS]]
    if not seeds:
        text = "No node matches: " + ", ".join(terms or [question])
        return {"seeds": [], "nodes": [], "edges": [], "text": text}

    adj = _adjacency(graph)
    seen = {s: 0 for s in seeds}
    frontier = deque((s, 0) for s in seeds)
    while frontier and len(seen) < MAX_NODES:
        node, dist = frontier.pop() if dfs else frontier.popleft()
        if dist >= depth:
            continue
        for neighbor, _ in sorted(adj[node], key=lambda p: p[0]):
            if neighbor not in seen and len(seen) < MAX_NODES:
                seen[neighbor] = dist + 1
                frontier.append((neighbor, dist + 1))

    by_id = {n["id"]: n for n in graph["nodes"]}
    kept = list(seen)
    edges = [e for e in graph["edges"]
             if e["source"] in seen and e["target"] in seen]
    # Seeds, then relations nearest the seeds, then the other nodes: when the
    # budget cuts the text, the node list goes first, not the relations.
    edges.sort(key=lambda e: (min(seen[e["source"]], seen[e["target"]]),
                              e["source"], e["target"]))

    def entry(nid):
        node = by_id.get(nid, {"id": nid})
        return ("- " + nid + " (" + str(node.get("kind", "?")) + ", "
                + _loc(node) + ")")

    lines = ["# Query: " + question, "", "## Best matches"]
    lines += [entry(nid) for nid in seeds]
    lines += ["", "## Relations"]
    lines += ["- " + e["source"] + " --" + e["rel"] + " " + _label(e)
              + "--> " + e["target"] for e in edges]
    lines += ["", "## Other nodes"]
    lines += [entry(nid) for nid in sorted(kept, key=lambda n: (seen[n], n))
              if nid not in seeds]
    return {"seeds": seeds, "nodes": kept, "edges": edges,
            "text": _trim("\n".join(lines), budget)}


def _children(graph, node_id):
    "Symbols a file or class holds: defines/contains targets and methods."
    out = set()
    for e in graph["edges"]:
        if e["source"] == node_id and e["rel"] in CHILD_RELS:
            out.add(e["target"])
    for e in graph["edges"]:
        if e["rel"] == "method_of" and (e["target"] == node_id
                                         or e["target"] in out):
            out.add(e["source"])
    return out


def affected(graph, node_id, depth=2, relations=None):
    """Return [{'id', 'depth', 'rel'}] for nodes that depend on node_id.

    A file or class counts as changed together with the symbols it holds, so
    callers of a file's functions show up as affected by that file.
    """
    rels = set(relations or DEPENDENCY_RELS)
    incoming = defaultdict(list)
    for e in graph["edges"]:
        if e["rel"] in rels:
            incoming[e["target"]].append(e)
    start = {node_id} | _children(graph, node_id)
    seen = set(start)
    out = []
    frontier = deque((n, 0) for n in sorted(start))
    while frontier:
        node, dist = frontier.popleft()
        if dist >= depth:
            continue
        for e in incoming[node]:
            src = e["source"]
            if src not in seen:
                seen.add(src)
                out.append({"id": src, "depth": dist + 1, "rel": e["rel"],
                            "confidence": e.get("confidence")})
                frontier.append((src, dist + 1))
    return out


def describe(graph, node_id):
    "Return a node's neighbors grouped by relation and direction, plus text."
    node = next((n for n in graph["nodes"] if n["id"] == node_id),
                {"id": node_id})
    outgoing, incoming = defaultdict(list), defaultdict(list)
    for e in graph["edges"]:
        if e["source"] == node_id:
            outgoing[e["rel"]].append({"id": e["target"],
                                       "confidence": e.get("confidence")})
        if e["target"] == node_id:
            incoming[e["rel"]].append({"id": e["source"],
                                       "confidence": e.get("confidence")})
    lines = [node_id + " (" + str(node.get("kind", "?")) + ", "
             + _loc(node) + ")"]
    for groups, arrow in ((outgoing, "-->"), (incoming, "<--")):
        for rel in sorted(groups):
            lines.append("  " + arrow + " " + rel + ":")
            for item in groups[rel]:
                tag = "[E]" if item["confidence"] == "EXTRACTED" else "[I]"
                lines.append("      " + tag + " " + item["id"])
    return {"id": node_id, "kind": node.get("kind"),
            "outgoing": dict(outgoing), "incoming": dict(incoming),
            "text": "\n".join(lines)}


def path_hops(graph, route):
    "Return one {'source','target','rel','confidence','direction'} per hop."
    index = {}
    for e in graph["edges"]:
        index.setdefault((e["source"], e["target"]), e)
    hops = []
    for a, b in zip(route, route[1:]):
        edge, direction = index.get((a, b)), "->"
        if edge is None:
            edge, direction = index.get((b, a)), "<-"
        edge = edge or {}
        hops.append({"source": a, "target": b, "rel": edge.get("rel", "?"),
                     "confidence": edge.get("confidence"),
                     "direction": direction})
    return hops
