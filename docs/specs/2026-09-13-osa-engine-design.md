# One Skill Army: Native Engine Design

Date: 2026-09-13
Status: implemented. Spec 1 (engine), Spec 2 (harness), Spec 3 (self-contained
orchestrator), and Spec 4 (bridge migration to the native engine) are done and
verified. Spec 4 was scoped as the bridge option: native `osa` is the primary
graph across the graphify skill, memory skill, AGENTS.md, and the /graphify
command, while osa-graph-stale.py remains for the HTML view and the optional
manual edge layer. Codex/Grok/Gemini/Antigravity still rely on instruction-file
injection (no confirmed per-turn hook schema); Antigravity has no adapter yet.

## Goal

Rebuild One Skill Army as a self-contained project that natively provides the
four capabilities it currently borrows from external packs, with no runtime
dependency on any of them:

| Borrowed from | Native capability |
|---|---|
| Ponytail | Code quality: the minimal-code reuse ladder, laziest solution that works |
| Caveman | Overhead compression: cut internal working/context overhead, never the implementation output |
| Superpowers | Discipline: structured workflow, TDD, systematic debugging, verification |
| Graphify | Project memory: a prebuilt structural graph so the LLM never rediscovers the project and reads the smallest useful context |

The deliverable is one architecture with three parts: a host-agnostic engine,
thin per-host harness adapters, and one orchestrator skill.

## Architecture

```
osa  (Python 3 stdlib, zero external deps)      the one engine / harness core
 ├─ osa index [path]    scan project -> .osa/graph.json + .osa/context.md + .osa/manifest.json
 ├─ osa context <q>     return the smallest useful context slice for a task (no repo re-scan)
 ├─ osa fresh [--auto]  manifest vs disk staleness; --auto reindexes only changed files
 └─ osa brief [--level] emit the harness directive: disciplines + overhead-compression rule + context pointer

host adapters (thin hooks, all shell out to osa)
 └─ claude · zcode · grok · cursor · codex · antigravity
    programmatic hook where the host allows it; instruction-file injection where it does not

orchestrator skill (the brain)
 └─ four native capabilities plus rails (anti-hallucination, git-safety, code-commenting)
```

### Runtime choice

Python 3 stdlib. The only component with real logic is the graph engine, and
that maps naturally onto `ast` and `hashlib`. The harness is just host config
that runs a command printing a directive, so adapters stay trivial shell. This
matches Graphify (Python) and Caveman's Codex adapter (a plain shell echo).

## Engine detail (Spec 1)

### Graph model

Deterministic only. The engine never invents an edge; that keeps
anti-hallucination true at the data layer.

- Nodes: `file`, `symbol` (function / class / const), `module`. Attributes:
  id, path, kind, line, lang.
- Edges: `imports` (file -> module/file), `defines` (file -> symbol),
  `calls` / `references` (symbol -> symbol, best effort, same language only),
  `contains`.

### Extractors

A registry mapping file extension to a parser. Graph quality scales with
language support but never requires a dependency.

- Python: `ast` parses imports, defs, classes, call sites. High fidelity.
- JS / TS: line and regex scan for import / require, export, function / class
  declarations, call sites. Best effort.
- Markdown / docs: headings and links as nodes and edges.
- Generic fallback: a file node plus a regex symbol scan; unknown extension
  yields a file node only.

### Ranking and context

Cheap, pure stdlib, no numpy.

- God nodes by degree plus fan-in / fan-out.
- Entrypoint heuristics: `main`, `index`, `cli`, `app`, `server`, `__main__`,
  high fan-in.
- `context.md` = entrypoints + top-N god nodes + one line per directory +
  a symbol-to-file index, trimmed to a token budget by dropping the lowest rank.
- `osa context <q>` resolves the query to nodes by name or path, walks a
  depth 1 to 2 neighborhood, and emits definitions, direct callers, and sibling
  files, capped to a budget.

### Freshness and layout

- `.osa/` at the project root holds `graph.json`, `context.md`,
  `manifest.json`, and optional `config.json`.
- manifest: `{version, built_at, files: {path: {sha256, mtime, size}}}`.
- `osa fresh`: diff disk against the manifest into stale / new / deleted;
  exit 0 fresh, 1 stale; `--auto` reindexes only changed files.
- config: token budget, include / exclude globs, language toggles, all
  defaulted so no config file is required.
- ignores: `.gitignore` plus built-ins (`.git`, `node_modules`, `.osa`,
  `__pycache__`, `dist`, `build`, `venv`, `.next`).

### Reuse

`skills/graphify/osa-graph-stale.py` already implements the scan, sha256
snapshot, staleness report, JSONL I/O, and a self-contained HTML renderer.
The engine reuses that logic for the freshness layer and visualization rather
than duplicating it; the new work is the deterministic extractors, ranking,
context digest, and brief.

## Harness detail (Spec 2)

The brief is re-asserted every turn, not only at session start. A mid-session
model switch (for example a `/model` change) does not fire SessionStart, so
per-turn re-injection through the host's prompt hook is the only robust way to
keep the disciplines active across a model switch. Each host adapter maps its
own hook events onto two engine calls: refresh-if-stale plus `osa brief` at
session start, and `osa brief` (idempotent, cheap) on every user prompt.

## Orchestrator detail (Spec 3)

One skill encoding the four native capabilities and the rails, dropping all
references to the external packs. It must state that the disciplines persist
across model switches and context compaction.

## Migration detail (Spec 4)

Remove the graphify Python-package dependency, fold or retire redundant skill
files, and point every adapter and command at the native engine.

## Build order

1. Core engine (this spec); everything depends on it.
2. Harness protocol and adapters, Claude and ZCode first, then the rest.
3. Orchestrator skill rewrite.
4. Migration and cleanup.

Within the engine, build bottom-up: extractors, then graph and ranking, then
index and manifest, then context, then brief, then fresh, then the CLI.
