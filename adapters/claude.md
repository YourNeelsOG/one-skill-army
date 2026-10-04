# Claude Code Adapter

## Install (plugin, recommended)

```bash
/plugin marketplace add YourNeelsOG/one-skill-army
/plugin install one-skill-army
```

The plugin ships skills, commands, and a SessionStart hook that injects the
orchestrator at startup and re-injects it after compaction.

## Install (script, recommended for the copy route)

```bash
scripts/install.sh claude            # install or upgrade under ~/.claude
scripts/install.sh claude --doctor   # installed vs source version
scripts/install.sh claude --uninstall
```

Re-running it is the upgrade: it prunes skills/commands retired in past
versions (e.g. the old `osa-map`, renamed to `mapit`), copies the current
set with the bundled `osa.pyz`, and stamps `~/.claude/.one-skill-army-version`.

## Install (manual)

```bash
mkdir -p ~/.claude/skills && cp -r skills/* ~/.claude/skills/
mkdir -p ~/.claude/commands && cp commands/*.md ~/.claude/commands/
```

A plain copy cannot prune, so on upgrades remove renamed items by hand
(`rm -rf ~/.claude/skills/graphify`). The script route avoids that.

## Anchor file

Claude Code reads `CLAUDE.md` and does not read `AGENTS.md`. In a project
where `AGENTS.md` is the canonical rule file, give `CLAUDE.md` a bare import:

```markdown
@AGENTS.md
```

Without that line, rules written to `AGENTS.md` are absent from Claude's
context at session start.

## Engine (osa)

The project-map engine ships bundled with the skills as
`~/.claude/skills/one-skill-army/osa.pyz` (or `python3 -m osa` from a repo
checkout). Build the map once per project, then let the agent read it:

```bash
python3 ~/.claude/skills/one-skill-army/osa.pyz index .   # build .osa/graph.json + context.md
python3 ~/.claude/skills/one-skill-army/osa.pyz context <term>   # smallest useful slice
```

The SessionStart hook refreshes the map and injects the orchestrator; the
UserPromptSubmit hook re-injects the brief every turn, so the disciplines
survive a mid-session model switch and context compaction.

## Skills (68, routed by the orchestrator)

The ten core disciplines (`memory`, `minimal-code`, `token-discipline`,
`workflow`, `test-driven-development`, `systematic-debugging`,
`verification-before-completion`, `anti-hallucination`, `code-commenting`,
`git-safety`) plus `input-discipline`, `army-commit`, `mapit`, and the
process skills `writing-plans`, `subagent-driven-development`, `code-review`,
and `using-git-worktrees`. Commands: `/army`, `/army-review`, `/army-audit`,
`/army-debt`, `/army-gain`, `/army-compress`, `/army-help`, `/mapit`.

The pack includes 50 adapted pstack skills in addition to these 18 OSA
disciplines. Each has a command wrapper. Use `/poteto-mode` for task routing
and `/setup-pstack` for model configuration. Resolve tools and models from the
current host; missing delegation runs sequentially. OSA rules remain
authoritative, and optional Bun helpers require separate dependency setup.

## Platform notes

- Claude follows SKILL.md instructions faithfully; keep `one-skill-army` as
  the single entry point and let it route.
- Claude is fluent and confident: anti-hallucination runs at full strictness;
  "verify or label" outranks token-discipline here.
- Subagents: the `Agent` tool exists, so workflow's "fresh subagent per task
  + diff review" path is active. Subagent success reports still get verified
  against the VCS diff.
- Memory: `.osa/memory/` is the store. If ai-memory's MCP server is also
  configured, route durable pages to it instead of duplicating.
- Hooks can enforce git-safety mechanically, e.g. a PreToolUse hook blocking
  any Bash call matching `push --force` / `--force-with-lease`.

## Defaults

- token-discipline: `full`
- Commit style: army-commit (terse conventional)
- git-safety: always on; force-push-blocking hook recommended
