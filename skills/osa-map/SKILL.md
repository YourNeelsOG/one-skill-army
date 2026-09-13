---
name: osa-map
description: >
  Persistent project-intelligence graph for the One Skill Army pack. The native
  osa engine auto-builds a deterministic graph from the code (no manual work,
  no external package); the agent reads the prebuilt context instead of
  re-discovering the project. Optional manual edges capture relationships the
  parser cannot see, and osa-graph-stale.py renders the HTML view. Use when
  starting work in an indexed project, when asked about project structure or
  dependencies, or when the user says osa-map or graph the project.
---

# osa-map - persistent project intelligence

Purpose: stop re-discovering a project's structure every conversation. The
graph stores what the project IS and how it CONNECTS; the agent queries it,
re-verifies only what changed, and reads files to confirm, not to explore.

Source of truth: the files on disk, always. The graph is an index. An edge is a
claim until confirmed against the file. If a file contradicts the graph, the
file wins: fix the graph, not the code.

## Native engine (primary, automatic)

The native `osa` engine builds the graph deterministically from the code with no
manual bookkeeping and no external dependency (pure Python standard library). It
ships bundled as `osa.pyz` beside the orchestrator skill, so it runs with no
install: `python3 <skills>/one-skill-army/osa.pyz <command>`, or `python3 -m osa
<command>` from a repo checkout.

- `python3 -m osa index .` scans the project and writes `.osa/graph.json`
  (files, symbols, imports, defines edges), `.osa/context.md` (the map the
  agent reads: entrypoints, most-connected nodes, directory layout), and
  `.osa/graph.html` (a self-contained force-directed view; `--no-html` skips
  it). It prints where the HTML landed so you can open it in a browser.
- Read `.osa/context.md` first, then `python3 -m osa context <term>` for the
  smallest useful slice: the matching nodes and their direct neighbors, so you
  find where something lives without scanning every file.
- `python3 -m osa fresh --auto` re-indexes only the files that changed.

The engine never invents an edge, so what it shows is real. Prefer it over broad
search for structure and dependency questions.

## Storage (per project: .osa/)

- `graph.json`: the native engine's deterministic graph (nodes + edges).
- `context.md`: the token-bounded project map the agent reads first.
- `manifest.json`: the engine's sha256 freshness baseline.
- `graph/`: the optional manual layer, described below.
- `graph.html`: the rendered visualization, open in a browser.

Every project carries its own graph: multi-project isolation is automatic.
Never merge graphs across projects.

## Optional manual layer (relationships the parser cannot see)

The native engine covers structural edges (imports, defines, calls within a
language). For semantic links it cannot infer (a route served by a controller,
a config that configures a service, a doc that documents a module), record them
by hand in `.osa/graph/edges.jsonl`, one JSON per line, with `evidence` and the
date:

`{"from": "src/auth.ts", "rel": "serves|configures|documents|tests", "to": "src/user.ts", "seen": "2026-09-12", "evidence": "observed in session"}`

The accumulation rule: write the edge the moment you learn it, with real
`evidence` (file:line or "observed in session"). An edge without evidence is a
rumor. Do not batch until "later": later never comes.

## Staleness and visualization

`osa-graph-stale.py` ships next to this skill and handles the freshness baseline
and the HTML view:

- `python3 "<osa-map skill dir>/osa-graph-stale.py" --update` rewrites the
  manifest baseline (run at task end).
- `python3 "<osa-map skill dir>/osa-graph-stale.py"` (no flag) reports which
  files changed (ADDED / MODIFIED / DELETED) since the last baseline.
- `python3 "<osa-map skill dir>/osa-graph-stale.py" --html` renders
  `.osa/graph/graph.html`: self-contained, no network, force-directed, drag
  nodes, hover for summaries, search to filter. Regenerate after meaningful
  graph changes.

For the native graph, `python3 -m osa fresh --auto` is the faster path; the
staleness script remains for the manual layer and the HTML view.

## Query discipline

- "Which file imports X?" / "Where is this function used?" / "What depends on
  Y?": query the native graph first with `osa context <term>`, then grep
  `.osa/graph/edges.jsonl` for any manual edges.
- Hit rate low or answer suspicious? Fall back to grep on the codebase, and
  write what you learn back into the graph.
- The graph saves tokens only if it is trusted: keep `evidence` real so future
  sessions can re-check a claim cheaply.

## Boundaries

- Never treat the graph as source of truth; never edit code to match the graph.
- The native engine is deterministic and re-runnable; rebuild it with
  `osa index` rather than hand-patching `graph.json`.
- Graph says A imports B but the file disagrees: rebuild or fix the edge the
  moment you see it.
- Do not put secrets in the graph; `.osa/` files can be committed.
