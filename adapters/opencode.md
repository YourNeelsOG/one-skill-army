# OpenCode Adapter

OpenCode (opencode.ai) reads `AGENTS.md` natively and loads JS plugins that
can register skills and inject system-prompt context every turn.

## Install

### Route A: local checkout (works today, no npm publish needed)

```bash
# global (every OpenCode session):
mkdir -p ~/.config/opencode/plugins
cp ".opencode/plugins/one-skill-army.mjs" ~/.config/opencode/plugins/

# or project-only:
mkdir -p ~/your-project/.opencode/plugins
cp ".opencode/plugins/one-skill-army.mjs" ~/your-project/.opencode/plugins/
```

Tell the plugin where the pack lives (it registers `skills/` and
`commands/` from there):

```bash
export OSA_REPO_ROOT="/absolute/path/to/one-skill-army"   # in your shell profile
```

Restart OpenCode. The plugin registers all 68 skills and the 58 commands
(`/army`, `/army-review`, `/army-audit`, `/army-debt`, `/army-compress`,
`/army-gain`, `/army-help`, `/mapit`) and appends a one-line reminder to the
system prompt every turn, the OpenCode equivalent of ZCode's UserPromptSubmit
hook, so the disciplines survive a mid-session model switch.

### Route B: git plugin (once this repo is published)

```json
{
  "plugin": ["one-skill-army@git+https://github.com/YourNeelsOG/one-skill-army.git"]
}
```

in `opencode.json` (global `~/.config/opencode/opencode.json` or project
root), then restart.

### Route C: instruction-only (zero plugins)

OpenCode is AGENTS-aware: copy `AGENTS.md` to the project root and the rules
load as instructions, with no hook injection and no commands. Weakest
enforcement, strongest portability.

## Platform notes

- The plugin's `experimental.chat.system.transform` re-asserts the rules
  every turn; without the plugin (route C) nothing re-injects after
  compaction, so lean on the memory skill's handoff discipline.
- Mode resolution matches every other host: `OSA_DEFAULT_MODE` env >
  `defaultMode` in the project's `.osa/config.json` > `full`. `off` disables
  the reminder injection.
- Verify: ask "what skills are active?" after restart; `/army-help` should
  render the reference card.

## Engine (osa)

The map engine runs as `python3 -m osa` from the `OSA_REPO_ROOT` checkout, or
as the bundled `python3 <skills>/one-skill-army/osa.pyz`. Build the map once
per project so the agent reads it instead of scanning:

```bash
python3 -m osa index .
python3 -m osa context <term>
python3 -m osa fresh --auto
```

The 68 skills include `mapit` plus the process skills `writing-plans`,
`subagent-driven-development`, `code-review`, and `using-git-worktrees`.

## Defaults

- token-discipline: `full`
- git-safety: always on
- memory: `.osa/memory/` shared across every host

## Poteto workflows

The 50 adapted pstack skills add matching commands, including `/poteto-mode`
and `/create-verification-skill`. OSA rules remain authoritative. Use available
host tools and models, with sequential fallback when delegation is absent.
Optional Bun helpers require separate runtime and dependency setup.
