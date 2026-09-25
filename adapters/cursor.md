# Cursor Adapter

## Install (plugin, if your Cursor version supports plugins)

Copy `.cursor-plugin/` into the project (or reference the repo); the
manifest registers `skills/`, `commands/`, and the SessionStart hook
(`hooks-cursor.json`).

## Install (rules files, always works)

```bash
mkdir -p ~/your-project/.cursor/rules
cp AGENTS.md ~/your-project/.cursor/rules/one-skill-army.mdc
```

Add frontmatter to the `.mdc` so it always applies:

```markdown
---
description: One Skill Army pack: minimal code, token discipline, workflow, TDD, anti-hallucination, memory, git-safety
alwaysApply: true
---
```

Commands become Cursor custom commands: copy each file from `commands/`
into `.cursor/commands/<name>.md`.

## Anchor file

`.cursor/rules/one-skill-army.mdc` with `alwaysApply: true`. Keep the pack
in ONE always-apply rule file rather than six glob-scoped ones, so rule
precedence stays predictable.

## Engine (osa)

The map engine ships bundled as `osa.pyz` beside the orchestrator skill (and
runs as `python3 -m osa` from a repo checkout). Build the map once per project:

```bash
python3 <skills>/one-skill-army/osa.pyz index .
python3 <skills>/one-skill-army/osa.pyz context <term>
```

With the plugin install, the SessionStart hook refreshes the map and the
UserPromptSubmit hook re-injects the brief every turn (survives a model
switch). With the rules-file install, the alwaysApply rule re-enters context,
but run `osa index`/`osa fresh --auto` yourself since there is no hook.

## Skills (18, routed by the orchestrator)

Ten core disciplines plus `input-discipline`, `army-commit`, `mapit`, and the
process skills `writing-plans`, `subagent-driven-development`, `code-review`,
`using-git-worktrees`. Commands: `/army`, `/army-review`, `/army-audit`,
`/army-debt`, `/army-gain`, `/army-compress`, `/army-help`, `/mapit`.

## Platform notes

- Tab completions do not read rules: after accepting large Tab suggestions,
  run a manual pass for em dashes, banner comments, and invented symbols
  (Tab pulls from open files and hallucinates).
- Cursor Bugbot is on the git-safety blocklist: keep it disabled on repos
  using this pack. Review = human or in-session subagent only.
- The SessionStart hook (plugin install) re-injects the pack after
  compaction; with rules-file install, the alwaysApply rule re-enters
  context automatically.

## Defaults

- token-discipline: `full`
- git-safety: always on; verify Bugbot is off
- memory: `.osa/memory/` shared with every other host
