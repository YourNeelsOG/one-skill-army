---
description: "mapit: map the project into a queryable knowledge graph with the native osa engine, bring it up to date with the latest changes, and answer questions from it (query, explain, path, affected). Every edge is labelled EXTRACTED or INFERRED."
---

Read the argument: `$ARGUMENTS`. Route on its first word. The native `osa`
engine is the only path needed: pure Python standard library, deterministic,
no external package. Use `python3 -m osa` from a checkout of this pack, or
`python3 <skills>/one-skill-army/osa.pyz` from an installed copy.

## (empty), `.`, or `update`: bring the map up to the latest changes

```
python3 -m osa update .
```

Incremental: only files whose content changed are parsed again; cross-file
links are then re-resolved over the whole project, so the result equals a full
build. Use `python3 -m osa update . --force` after a big refactor, or
`python3 -m osa index .` for a first full build. Report the node/edge counts
and that `.osa/graph.html` (interactive view) and `.osa/GRAPH_REPORT.md`
(full report) were written. Before updating, append any manual edges learned
this session to `.osa/graph/edges.jsonl` with evidence.

## `status`

```
python3 -m osa fresh .
```

Up to date: summarize `.osa/context.md`. Stale: list what changed and offer
`/mapit update`. Not indexed yet: offer `python3 -m osa index .`.

## `query <question>`

```
python3 -m osa query "<question>"
```

Returns the best-matching nodes and the subgraph around them, each edge
tagged `[E]` (extracted from syntax) or `[I]` (inferred, heuristic). Options:
`--depth N` (default 2), `--budget N` tokens (default 2000), `--dfs`,
`--json`. Answer from that output; open a real file only to confirm before
acting.

## `explain <node>`, `path <a> <b>`, `affected <node>`, `god-nodes`

```
python3 -m osa explain "<node>"
python3 -m osa path "<a>" "<b>"
python3 -m osa affected "<node>" --depth 2
python3 -m osa god-nodes --top 10
```

Node names can be ids (`osa/cli.py::main`), plain names (`main`), or a unique
substring. An ambiguous name exits 2 and prints candidates: pick one and
rerun. `affected` answers "what breaks if I change this".

Rules that always hold: source of truth is the files; the graph is an index;
INFERRED edges are claims to verify; manual edges carry evidence; never merge
graphs across projects; if `graphify-out/` exists, use the external graphify
tool instead.
