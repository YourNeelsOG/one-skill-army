# Gemini CLI Adapter

## Install

```bash
# Gemini CLI reads GEMINI.md from the repo root:
cp AGENTS.md ~/your-project/GEMINI.md

# skills + commands + osa engine, with prune-on-upgrade and a version receipt:
scripts/install.sh gemini            # install or upgrade under ~/.gemini
scripts/install.sh gemini --doctor   # installed vs source version
```

Re-running `scripts/install.sh gemini` is the upgrade: it prunes retired items
(e.g. `osa-map` renamed to `mapit`) and restamps the version. A plain
`cp -r skills/* ~/.gemini/skills/` also works but cannot prune renames.

## Anchor file

`GEMINI.md` in the repo root (copy of `AGENTS.md`). If the project keeps
both, make `GEMINI.md` a pointer to `AGENTS.md` so rules never fork.

## Engine (osa)

The map engine ships bundled as `~/.gemini/skills/one-skill-army/osa.pyz` (or
`python3 -m osa` from a repo checkout). Build the map once per project:

```bash
python3 ~/.gemini/skills/one-skill-army/osa.pyz index .
python3 ~/.gemini/skills/one-skill-army/osa.pyz context <term>
```

Gemini CLI has no per-turn context-injection hook, so read `.osa/context.md`
at task start and run `osa fresh --auto` after edits rather than expecting an
auto-refresh.

## Skills (69, routed by the orchestrator)

Ten core disciplines plus `input-discipline`, `army-commit`, `mapit`, and the
process skills `writing-plans`, `subagent-driven-development`, `code-review`,
`using-git-worktrees`. Commands: `/army`, `/army-review`, `/army-audit`,
`/army-debt`, `/army-gain`, `/army-compress`, `/army-help`, `/mapit`.

The pack includes 50 adapted pstack skills in addition to these 19 OSA
disciplines. Each has a command wrapper. Use `/poteto-mode` for task routing
and `/setup-pstack` for model configuration. Resolve tools and models from the
current host; missing delegation runs sequentially. OSA rules remain
authoritative, and optional Bun helpers require separate dependency setup.

## Platform notes

- Gemini handles long SKILL.md files well: load the full orchestrator; no
  need to trim.
- Gemini CLI has broad tool access (Google Cloud, MCP): git-safety's
  per-action approval covers those tools too. Assume nothing outside the
  repo is fair game.
- Token-discipline `full`: Gemini's summaries drift verbose; the
  never-compress list keeps code and errors intact while trimming narration.
- Gemini Ultra-class on long autonomous runs: keep the anti-hallucination
  ledger habit, and the memory skill's compaction protocol matters most on
  the longest runs (write the handoff early, re-read after compaction).

## Defaults

- token-discipline: `full`
- git-safety: always on, includes MCP/cloud tool calls
- memory: `.osa/memory/` shared with every other host
