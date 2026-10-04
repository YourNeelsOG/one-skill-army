# ZCode Adapter

ZCode is the reference host for this pack: the installer
([`scripts/install-zcode.sh`](../scripts/install-zcode.sh)) automates
everything below.

## Install

```bash
scripts/install-zcode.sh                # user scope: every workspace
scripts/install-zcode.sh --upgrade      # re-sync a stale install: prune orphans, copy new, restamp version
scripts/install-zcode.sh --agents-compat  # also ~/.agents/ (shared with Claude/Codex/Cursor)
scripts/install-zcode.sh --doctor       # verify an install + show version drift
scripts/install-zcode.sh --uninstall    # remove everything; project memory is kept
```

Upgrading: user-scope files under `~/.zcode/` do not change when you pull a new
version of this repo. Re-run the installer to sync them. It records the version
in `~/.zcode/.one-skill-army-version`, prunes skills/commands retired in past
versions (for example the old `osa-map` skill and `/osa-map` command, renamed
to `mapit`), and `--doctor` reports drift so you know when a re-sync is due.

## Where things land

| Resource | User scope | Notes |
|---|---|---|
| Skills | `~/.zcode/skills/<name>/SKILL.md` | 69 skills, every workspace |
| Commands | `~/.zcode/commands/<name>.md` | `/army`, `/army-review`, `/army-audit`, `/army-debt`, `/army-gain`, `/army-compress`, `/army-help`, `/mapit` |
| Engine | `~/.zcode/skills/one-skill-army/osa.pyz` | the bundled map engine, runs standalone |
| Hook script | `~/.zcode/hooks/one-skill-army-session-start` | stable path; survives repo moves |
| Hook config | `~/.zcode/cli/config.json` -> `hooks` | merged, never overwritten; backup created |
| Instruction anchor | `~/.zcode/AGENTS.md` or `<repo>/AGENTS.md` | optional; the pack works via skills + hook |
| Project memory | `<repo>/.osa/memory/` | created on first write; commit it like code |

Workspace scope alternative: `<repo>/.zcode/skills/` versions the pack with
the repo for a team. User scope shadows workspace on name conflicts.

## Isolation from other tools

This install touches ONLY ZCode-owned paths: `~/.zcode/{skills,commands,hooks}`
and `~/.zcode/cli/config.json`. No other application reads those locations,
so the install cannot change how Claude Code, Codex, Cursor, Gemini, or any
other agent behaves. Symmetrically, they get none of the pack's rules until
they are installed per their own adapter. Two things ARE shared across
hosts, by design:

- **Project files**: `AGENTS.md` in a repo root, `.osa/memory/`, and `osa:`
  comments are plain files any agent can read. A host without the pack can
  still see the memory and the anchor, but nothing *enforces* the rules
  there: git-safety rails only bind agents that loaded the pack.
- **`--agents-compat`**: additionally copies skills/commands to
  `~/.agents/{skills,commands}`, the cross-tool scope ZCode reads as a
  fallback. Tools with dedicated directories (Claude Code reads
  `~/.claude/skills`) ignore it unless they support the convention.

## Install difficulties this adapter solves

These are the traps hit while building the installer:

1. **Commands silently drop arguments.** A command file that never
   references `$ARGUMENTS` loses everything the user typed after the command
   name (`/army ultra` became "no argument"). Every arg-taking command here
   includes `$ARGUMENTS` plus an `argument-hint` in frontmatter.
2. **Config-file hooks are off by default.** `hooks.events.SessionStart`
   does nothing until `"hooks": { "enabled": true }` is set. Plugin hooks
   enable the runner automatically; config hooks do not.
3. **Hardcoded repo paths break.** The hook command originally pointed into
   this repo (whose path contains spaces, a quoting trap). The installer
   copies the hook script to `~/.zcode/hooks/` and registers that stable path.
4. **Naive config writes destroy existing setup.** `config.json` may already
   hold MCP servers and plugins. The installer merges JSON (backup first,
   validates after) and deduplicates its own entries idempotently.
5. **A failing hook errors every session start.** A hook that exits
   non-zero or prints non-strict JSON raises errors at startup. The hook
   script therefore always exits 0, always emits exactly one JSON object,
   and degrades to a warning message if its files are missing.
6. **Skill name shadowing.** First same-named skill wins in discovery
   order; the pack's generic names (`memory`, `workflow`) shadow any other
   copy at lower precedence. If you install a second pack with colliding
   names, remove one or namespace directories.
7. **Context cost.** 18 skill descriptions load into every session. That is
   the price of auto-triggering; delete skill directories you do not want
   (e.g. keep only `one-skill-army` to route manually).

## Engine (osa)

The installer copies the whole `skills/` tree, so the bundled map engine lands
at `~/.zcode/skills/one-skill-army/osa.pyz` and runs standalone (no PYTHONPATH):

```bash
python3 ~/.zcode/skills/one-skill-army/osa.pyz index .     # build the map
python3 ~/.zcode/skills/one-skill-army/osa.pyz context <term>
python3 ~/.zcode/skills/one-skill-army/osa.pyz fresh --auto
```

The SessionStart hook injects the orchestrator and the map pointer; the
UserPromptSubmit hook re-injects the brief every turn, so the disciplines
survive a mid-session model switch.

## Plugin route

Settings -> Plugin Management -> Discover -> add this repo as a local
marketplace (`.claude-plugin/marketplace.json` and the ZCode-native
`.zcode-plugin/plugin.json` are both present). Plugin installs get the hook
enabled automatically; no config edit needed.

## Defaults

- token-discipline: `full`
- git-safety: always on (hook can be paired with a PreToolUse force-push blocker)
- memory: `.osa/memory/` shared across every host and agent

## Poteto workflows

The 50 adapted pstack skills add matching commands, including `/poteto-mode`
and `/create-verification-skill`. OSA rules remain authoritative. Use available
host tools and models, with sequential fallback when delegation is absent.
Optional Bun helpers require separate runtime and dependency setup.
