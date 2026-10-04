# LLM Adapters

The rules are identical on every platform; only the install location, the
instruction file the host reads, and the intensity defaults differ. Follows
the convention ai-memory documents: Claude Code reads `CLAUDE.md` and does
NOT read `AGENTS.md`, so the `CLAUDE.md` anchor must be a `@AGENTS.md`
import line; most other hosts read `AGENTS.md` natively.

| Host | Adapter | Instruction file it reads | Install |
|---|---|---|---|
| ZCode | [zcode.md](zcode.md) | `AGENTS.md` / `~/.zcode/AGENTS.md` | `scripts/install-zcode.sh` (automated) |
| Claude Code | [claude.md](claude.md) | `CLAUDE.md` (or `@AGENTS.md` import) | plugin marketplace or `~/.claude/skills` |
| Codex CLI | [codex.md](codex.md) | `AGENTS.md` | `~/.codex` or plugin |
| Grok Build CLI | [grok.md](grok.md) | `AGENTS.md` | `grok plugin install` + `config.toml` enable (plugins off by default; hooks can't inject) |
| Cursor | [cursor.md](cursor.md) | `.cursor/rules/*.mdc` | `.cursor-plugin` or rules files |
| Gemini CLI | [gemini.md](gemini.md) | `GEMINI.md` | `~/.gemini` + copy anchor |
| OpenCode | [opencode.md](opencode.md) | `AGENTS.md` | `.opencode/plugins/one-skill-army.mjs` (registers skills + commands + per-turn reminder) |

## Anchor files in this repo

- [`AGENTS.md`](../AGENTS.md): the canonical, complete rules. All hosts read
  it directly or via import.
- `hooks/session-start`: injects the orchestrator at session start and after
  compaction (Claude Code and Cursor plugin installs). Without the hook, the
  AGENTS.md anchor carries the same rules.
- `.osa/memory/`: created by the memory skill at runtime; the shared
  cross-agent, cross-host project memory.
- `skills/one-skill-army/osa.pyz`: the bundled map engine. It travels with the
  skills, so after any install run `python3 <skills>/one-skill-army/osa.pyz
  index .` once per project (or `python3 -m osa` from a checkout). The agent
  then reads `.osa/context.md` instead of re-scanning the tree.

The pack is 68 skills (routed by `one-skill-army`) and 58 commands. Beyond the
ten core disciplines it adds `input-discipline`, `army-commit`, `mapit`, and
the process skills `writing-plans`, `subagent-driven-development`,
`code-review`, and `using-git-worktrees`. Hosts with hooks (Claude, Cursor,
ZCode, OpenCode) re-inject the brief every turn so the rules survive a model
switch; the rest rely on the instruction anchor.

## Intensity defaults per host

| Host | token-discipline | Why |
|---|---|---|
| Claude Code | full | Faithful instruction following; terse loses nothing |
| Codex | lite prose / ultra commits | Cost lives in reasoning, not visible prose |
| Grok | full | Chatty default; ultra can drop needed nuance |
| Cursor | full | Agent mode; Tab completions bypass rules entirely |
| Gemini | full | Handles long SKILL.md well; summaries drift verbose |

Never dialed by intensity: anti-hallucination, verification, code-commenting,
git-safety, memory-safety. Those have no off switch.

## Poteto workflows

The 68 skills comprise 18 OSA disciplines and 50 adapted pstack workflows.
The latter each have a command wrapper. Named subagent prompts ship with the
skills, so hosts can use generic delegates or sequential execution. Optional
Bun helpers are separate from the dependency-free Python engine.
