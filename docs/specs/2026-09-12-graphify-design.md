# Graphify (One Skill Army) - Design Spec

Date: 2026-09-12. Status: approved by user in chat (approach selected:
agent-maintained + tiny script; visualization added by user).

## Purpose

Persistent project-intelligence layer for the One Skill Army pack. The
agent stops re-discovering project structure every conversation: it loads a
stored graph, queries relationships, and only inspects files to confirm.
Source code stays the source of truth; the graph is an index that can go
stale and says so.

## Components

1. `skills/graphify/SKILL.md`: the discipline. When to load, how to query,
   how to record edges while reading code, staleness rules, HTML rendering.
2. `scripts/osa-graph-stale.py` (python3, stdlib only, the only code):
   - No args: compare working tree to `.osa/graph/manifest.jsonl`, print
     ADDED / MODIFIED / DELETED between OSA-GRAPH-STALE / END markers plus
     one human summary line. Exit 0 always. No manifest: say how to create.
   - `--update`: rewrite the manifest from the current tree.
   - `--html`: render `.osa/graph/graph.html` from nodes + edges.
   - Scan skips: `.git`, `node_modules`, `.osa`, `.venv`, `venv`,
     `__pycache__`, `dist`, `build`, `.next`, `.env*`, files over 2 MB,
     files with a null byte in the first 8 KB.
3. `commands/graphify.md`: `/graphify status|update|query` card.
4. Edits: `skills/memory/SKILL.md` (own-graph route at session start),
   `AGENTS.md` section 0 (same route, one line), `skills/one-skill-army/
   SKILL.md` routing table (structure/dependency questions row),
   `tests/test_structure.py` (structure + behavioral tests).

## Storage, per project: `.osa/graph/` (multi-project isolation is
automatic; each repo carries its own graph)

- `GRAPH.md`: agent-facing map: project purpose, entrypoints, module map,
  key relationships, gotchas, last-verified date. Read at session start.
- `nodes.jsonl`: `{"id": "src/auth.ts", "kind": "file|function|class|
  route|service|model|config|doc", "summary": "one line"}`.
- `edges.jsonl`: `{"from", "rel": "imports|calls|tests|serves|configures|
  documents|builds", "to", "seen": "YYYY-MM-DD", "evidence"}`.
- `manifest.jsonl`: `{"path", "sha256", "bytes"}`, script-written.
- All plain text, committed by default guidance.

## Workflow

- Session start (`.osa/graph/` present): read GRAPH.md, run the script,
  re-read only listed files, answer from the graph, confirm in files before
  risky edits.
- During tasks: every relationship discovered while reading code is
  appended to edges.jsonl immediately, with evidence and date.
- Task end: `--update` refreshes the manifest; handoff notes graph state.
- Truth rule: an edge is a claim; conflict with a file = file wins, fix
  the edge.

## Visualization

`--html` writes `.osa/graph/graph.html`: one self-contained file, inline
CSS + vanilla-JS canvas force-directed layout, no external URLs (works
offline). Nodes colored by kind, drag to arrange, hover shows summary,
search box filters, legend included. Empty graph renders a placeholder
explaining how to fill it.

## Non-goals (v1)

No AST parsing (agent-extracted edges; skill holds grep heuristics as
fallback), no cross-project hub, no MCP server, no daemon, no auto-install
of the script into projects (run from the pack root; documented upgrade
path), rename detection beyond delete+add pairing by the agent. If a
project needs deterministic edges, the existing external graphify-tool
route stays.

## Testing (TDD, extend tests/test_structure.py)

Behavioral (temp dirs): stale detection for add/modify/delete; --update
writes manifest with correct hashes; --html generates a self-contained file
containing node and edge ids and no "https://". Structural: skill and
command present with frontmatter; memory skill, AGENTS.md, and orchestrator
reference the own-graph route.
