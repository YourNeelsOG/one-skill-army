---
description: "osa-map: build, query, or refresh the project's persistent knowledge graph via the native osa engine (.osa/graph.json + context.md). One-shot: status, update, or query."
---

Read the argument: `$ARGUMENTS`. Route on it. The native `osa` engine is the
primary path; it builds the graph deterministically with no external package.

## status (or empty)

Report freshness and the map:

```
python3 -m osa fresh .
```

If it reports the index is up to date, summarize `.osa/context.md` (entrypoints,
most-connected nodes). If it lists changed files, say what changed. Not indexed
yet? Say the first step is `python3 -m osa index .` and offer to run it.

## update

Rebuild the graph and refresh, then report:

```
python3 -m osa index .
python3 -m osa fresh --auto
```

For the optional HTML view of the manual edge layer, also run the osa-map
skill's `osa-graph-stale.py --html`. Before updating, apply any pending manual
edges learned this session to `.osa/graph/edges.jsonl` with evidence.

## query [question]

Answer from the graph, not the filesystem:

```
python3 -m osa context "$ARGUMENTS"
```

Read `.osa/context.md` for the overall map. Open a real file only to confirm
before acting, or when the graph has no answer (then rebuild with
`osa index`). Missing or empty graph? Say so and offer to build it.

Rules that always hold: source of truth is the files; the graph is an index;
manual edges carry evidence; never merge graphs across projects; if
`graphify-out/` exists, use the external graphify tool instead.
