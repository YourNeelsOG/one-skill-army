<p align="center">
  <strong>One Skill Army</strong>
</p>

<p align="center">
  <strong>One skill. Your agent writes less, spends less, forgets nothing, and never bluffs.</strong><br>
  Four proven ideas, rebuilt as one self-contained pack with its own engine. No external packs required.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/skills-18-blue" alt="18 skills">
  <img src="https://img.shields.io/badge/engine-zero_dependencies-brightgreen" alt="zero deps">
  <img src="https://img.shields.io/badge/tests-81_passing-brightgreen" alt="81 tests">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
</p>

<p align="center">
  <a href="#see-it">See it</a> ·
  <a href="#why">Why</a> ·
  <a href="#what-you-get">What you get</a> ·
  <a href="#the-osa-engine">Engine</a> ·
  <a href="#install">Install</a> ·
  <a href="#commands">Commands</a> ·
  <a href="#how-it-compares">Compare</a> ·
  <a href="#faq">FAQ</a> ·
  <a href="#contributing">Contribute</a>
</p>

---

## See it

**Getting oriented in a project:**

<table>
<tr>
<th width="50%">Plain agent</th>
<th width="50%">With One Skill Army</th>
</tr>
<tr>
<td valign="top">

Greps across the tree, opens dozens of files, reads ~150,000 tokens, and still asks where things live.

</td>
<td valign="top">

Reads one prebuilt map of ~700 tokens and already knows the entrypoints, the hubs, and where each thing lives. **Measured: 99% fewer tokens to get oriented.**

</td>
</tr>
</table>

**Answering a question:**

<table>
<tr>
<th width="50%">Plain agent</th>
<th width="50%">With One Skill Army</th>
</tr>
<tr>
<td valign="top">

> The re-render is likely because a new object reference is created each render; React's shallow comparison then treats it as changed and re-renders. Consider useMemo.

Writes 180 new lines. Says "this should work."

</td>
<td valign="top">

> New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`.

Reuses what exists, writes 30 lines, runs the test, shows the proof.

</td>
</tr>
</table>

## Why

Your AI coding assistant is capable but has bad default habits: it writes too much code, wastes words, re-learns your project every session, and sometimes invents APIs that do not exist. One Skill Army is a set of standing rules plus one small tool that fix those habits automatically. You install it once; the good behavior comes free on every task after that.

It brings together the four best ideas in agent tooling and reimplements each one natively, so it depends on none of them:

| Idea | What it does here |
|---|---|
| write the least code | reuse before build, the laziest solution that works |
| use fewer tokens | compress the thinking and context overhead, never the actual output |
| work with discipline | brainstorm, plan, test-first, debug from root cause, verify before "done" |
| remember the project | a deterministic graph so the agent reads a small map, not the whole tree |

## What you get

- **Better code.** A reuse ladder runs before any new code: does it need to exist, is it already here, does the standard library or platform do it, can it be one line. Bug fixes go to the root cause, not a patch.
- **Fewer tokens.** Terse working notes and a small context map, while code, commands, numbers, and error strings stay exact. Overhead shrinks; the answer never does.
- **Trustworthy output.** No claim about code it has not read this session, no invented functions, no "done" without fresh test evidence.
- **Project memory.** The `osa` engine maps the codebase once so the agent stops rediscovering it, and stays oriented across sessions and model switches.
- **Hard safety rails, always on.** Never force push, never open a PR or turn on an AI code reviewer without asking, no em dashes in code, structural comments for the next developer.

### The disciplines

`memory` · `minimal-code` · `token-discipline` · `workflow` · `test-driven-development` · `systematic-debugging` · `verification-before-completion` · `anti-hallucination` · `code-commenting` · `git-safety` · `input-discipline` · `writing-plans` · `subagent-driven-development` · `code-review` · `using-git-worktrees` · `army-commit` · `osa-map`

They are composable, and [`skills/one-skill-army/SKILL.md`](skills/one-skill-army/SKILL.md) is the single orchestrator that routes to them. One file is enough for an agent to follow the whole system.

Priority when they conflict, safety first: **git-safety > anti-hallucination > verification > memory > code-commenting > minimal-code > workflow > token-discipline.** A safety rail is never traded for speed.

## The osa engine

`osa` is the one piece of real code: pure Python standard library, zero external dependencies. It builds a deterministic graph of any project and serves the smallest useful slice, with no LLM in the loop, so it is free, instant, and never invents a connection.

It ships as a single bundled file, `osa.pyz`, inside the skills, so it runs anywhere with no install and no path setup: `python3 ~/.claude/skills/one-skill-army/osa.pyz <command>` (or `python3 -m osa <command>` from a repo checkout). The commands below use the short `osa` alias from the install step.

```bash
osa index .                      # build the map: graph.json + context.md + graph.html
osa context <term>               # smallest useful slice for a task, no repo scan
osa fresh --auto                 # re-index only the files that changed
osa explain <node>               # a node's role: degree, community, betweenness
osa path <a> <b>                 # shortest path between two parts of the code
osa export html                  # self-contained force-directed view (or graphml)
osa measure                      # how many tokens the map saves vs reading the tree
osa brief                        # the always-on discipline directive the hooks inject
```

The map carries real analysis with no model call: most-central files (betweenness), clusters (community detection), surprising cross-module links, and questions the graph can answer. On this repo `osa measure` reports about 99% fewer tokens to get oriented.

## Install

Installing means putting these files where your AI tool already looks. Two pieces:

1. **The skills** (the instruction files the AI reads) go in your tool's skills folder, once per machine.
2. **The rules file and the project map** go in each project you work on.

### Start here (Claude Code)

```bash
# 1. Install the skills (osa engine ships inside them). The installer prunes
#    old/renamed items and records the version, so re-running it upgrades:
scripts/install.sh claude          # or: gemini, agents, or --dir <path>

# 2. Optional: a short alias for the shipped engine
alias osa='python3 ~/.claude/skills/one-skill-army/osa.pyz'

# 3. In each project, build the map so the agent knows the codebase
osa index .
```

(A plain `cp -r skills/* ~/.claude/skills/` also works, but cannot prune
renamed items on later upgrades; the installer can.)

To auto-load the rules at the start of every session, add a `CLAUDE.md` at your project root containing one line, `@AGENTS.md`, and copy this repo's [`AGENTS.md`](AGENTS.md) next to it. Claude reads `CLAUDE.md`, not `AGENTS.md`, so the one-line import points it at the full rules. Prefer one click? Install this repo as a Claude plugin; that also wires the session hook, which re-loads the rules every turn and keeps them alive across a model switch.

### Other tools

Same rules, different folder and filename. One short note per tool lives in [`adapters/`](adapters/README.md):

| Tool | Install | Rules file it reads |
|---|---|---|
| ZCode | `scripts/install-zcode.sh` (does everything) | `AGENTS.md` |
| Claude Code | `~/.claude/skills` or plugin | `CLAUDE.md` (imports `AGENTS.md`) |
| Codex CLI | `~/.codex` or plugin | `AGENTS.md` |
| Cursor | `.cursor-plugin` or rules files | `.cursor/rules/*.mdc` |
| Gemini CLI | `~/.gemini` | `GEMINI.md` |
| Grok | `grok plugin install` (enable in `config.toml`) | `AGENTS.md` |
| OpenCode | `.opencode` plugin | `AGENTS.md` |

### Verify

```bash
python3 tests/test_structure.py
```

## Upgrading

Check what you have against the source: `python3 -m osa version` (or
`osa version` with the alias). The source version lives in `osa/__init__.py`.

- **ZCode**: re-run the installer. It is the upgrade: it prunes skills and
  commands retired in past versions (so a rename like `graphify` to `osa-map`
  leaves no orphan), copies the current set, and restamps the version.
  ```bash
  scripts/install-zcode.sh --upgrade     # or just re-run: scripts/install-zcode.sh
  scripts/install-zcode.sh --doctor      # shows installed vs source version + any drift
  ```
- **Claude Code, Gemini, or any copy-based host**: run the generic installer.
  Like the ZCode one, it prunes retired items, copies the current set (osa
  engine included), and stamps the version, so re-running it is the upgrade.
  ```bash
  scripts/install.sh claude              # or: gemini, agents, or --dir <path>
  scripts/install.sh claude --doctor     # installed vs source version
  ```
- **Plugin installs** (Claude Code, Cursor, Codex, Grok, OpenCode): if you
  installed through the host's plugin manager instead, upgrade there (refresh
  the marketplace, then reinstall or `plugin update`). The manifests carry the
  version, so the host sees the new release.
- **Raw copy** (no installer): `cp -r skills/*` cannot prune, so remove renamed
  items by hand, e.g. `rm -rf ~/.claude/skills/graphify` (renamed to osa-map).

After any upgrade, start a new session so the pack reloads, and run
`python3 -m osa index .` to rebuild the map with the latest engine.

## Commands

Slash commands (once installed in your tool):

| Command | What it does |
|---|---|
| `/army [lite\|full\|ultra\|off]` | set intensity: prose compression and ladder strictness |
| `/army-review` | review a diff: over-engineering, invented symbols, safety regressions |
| `/army-audit` | whole-repo audit: reinvented wheels, dead code, dependency sprawl |
| `/army-debt` | harvest `osa:` shortcut markers into a ledger so deferrals do not rot |
| `/army-gain` | measured-impact scoreboard, honest counted numbers only |
| `/army-compress` | compress a memory or instruction file to terse, with a backup |
| `/army-help` | reference card: levels, skills, commands |
| `/osa-map [status\|update\|query]` | build, refresh, or query the project map via `osa` |

## How it compares

The four ideas that inspired this pack are excellent. Here is the honest picture of where One Skill Army stands against each.

| Against | We match or beat | They still lead |
|---|---|---|
| minimal-code idea | same reuse ladder, plus the review/audit/debt commands | published head-to-head benchmark numbers |
| token idea | overhead compression with the output kept exact | a wire-level proxy and cloud spend analytics |
| workflow idea | the high-value process skills, native | a larger library of process skills |
| project-graph idea | deterministic graph, analysis, exports, free and instant | LLM-inferred edges and PDF, image, and video ingest |

Our deliberate trade: everything the graph does is deterministic, dependency-free, and costs no tokens to build. The features we do not match all require an LLM in the loop or an external service, which is exactly what "self-contained" rules out.

## FAQ

**Do I need an API key or an internet connection?** No. The engine is pure standard library and runs offline.

**Will it slow me down?** The map is built once and updated incrementally. Reading a small map is faster and cheaper than scanning the repo every session.

**Does it change my code style or my tools?** It adds standing rules and one map file per project (`.osa/`). It does not touch your code unless you ask it to.

**What if I only copy the skills, not the whole repo?** Everything works. The engine ships bundled as `osa.pyz` inside the skills, so `python3 ~/.claude/skills/one-skill-army/osa.pyz` runs with no repo checkout and no path setup.

**Can I turn the terse mode off?** Yes: `/army off`, or set the level to `lite`, `full`, or `ultra`. Safety rails never turn off.

## Philosophy

Most agent code is too long, most agent prose is too wordy, most agent workflows skip straight to typing, and most agents forget your project overnight. One Skill Army inverts all four: climb down the ladder before building, squeeze the words but never the facts, plan before typing, and keep a map so you never start blind.

## Contributing

Issues and pull requests are welcome; this is an open project. Before opening a PR:

1. Run the suite: `python3 tests/test_structure.py` plus every `tests/test_*.py` (all must pass).
2. Keep the engine pure standard library, zero dependencies; that constraint is the point.
3. Match the pack conventions: no em dashes anywhere, structural comments over noise, and the laziest solution that works.
4. If you touch `osa/`, rebuild the bundle with `python3 scripts/build-osa.py` so the shipped `osa.pyz` does not drift.

By contributing you agree your contributions are licensed under the repo's MIT license.

## License

MIT
