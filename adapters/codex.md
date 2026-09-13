# Codex CLI Adapter

## Install

```bash
# Codex reads AGENTS.md natively from the repo root; the anchor is enough:
cp AGENTS.md ~/your-project/AGENTS.md   # skip if the project already has one; merge instead

# plugin-style setup if your Codex build supports it:
cp .codex-plugin/plugin.json ~/.codex/plugins/one-skill-army.json
```

The `.codex-plugin/plugin.json` points Codex at `AGENTS.md` (instructions),
`skills/`, and `commands/`.

## Anchor file

`AGENTS.md` in the repo root is Codex's native instruction file. Nothing
extra needed.

## Engine (osa)

The map engine ships bundled as `osa.pyz` inside the skills, and also runs as
`python3 -m osa` from a repo checkout. Build the map once per project:

```bash
python3 -m osa index .        # or: python3 <skills>/one-skill-army/osa.pyz index .
python3 -m osa context <term> # smallest useful slice, no repo scan
```

Codex has no per-turn context-injection hook, so the map does not auto-refresh:
run `osa fresh --auto` after large edits, and read `.osa/context.md` at the
start of a task instead of re-scanning the tree.

## Skills (18, routed by the orchestrator)

Ten core disciplines plus `input-discipline`, `army-commit`, `osa-map`, and the
process skills `writing-plans`, `subagent-driven-development`, `code-review`,
`using-git-worktrees`. Commands: `/army`, `/army-review`, `/army-audit`,
`/army-debt`, `/army-gain`, `/army-compress`, `/army-help`, `/osa-map`.

## Platform notes

- Codex spends most tokens in reasoning, not visible prose: token-discipline
  `lite` for replies, `ultra` for commit messages and status lines. Cutting
  visible prose harder mainly inflates thinking on reasoning models.
- Reasoning models "know" APIs that don't exist in your pinned version:
  anti-hallucination's verify-in-fetched-docs rule applies double. Pin
  versions when checking docs.
- Sandbox/approval modes: run with the write sandbox so git-safety has a
  mechanical backstop; never grant unattended network + git credentials
  together. Force push and PR creation require interactive approval anyway
  when the user must approve commands.

## Defaults

- token-discipline: `lite` prose / `ultra` commits
- git-safety: always on
- memory: `.osa/memory/` committed to the repo, shared with every other host
