# Grok Build CLI Adapter

Grok Build CLI installs packs through the xAI plugin marketplace, but
plugins are DISABLED by default and Grok lifecycle hooks cannot inject
instructions. The AGENTS.md anchor therefore carries the rules; the plugin
carries the skills and commands.

## Install

### Route A: plugin (skills + slash commands)

```bash
grok plugin install YourNeelsOG/one-skill-army --trust
```

(Once this repo is added to a marketplace Grok knows; until then, use the
local-checkout route below.) Plugins are off by default; enable:

```toml
# ~/.grok/config.toml
[plugins]
enabled = ["one-skill-army"]
```

Restart the session. Verify with `grok inspect`; skills appear as
`/army`, `/army-review`, `/army-audit`, `/army-debt`, `/army-compress`,
`/army-gain`, `/army-help`, `/osa-map`. Grok can auto-invoke skills from their
descriptions; use `/army lite|full|ultra` to make it explicit.

### Route B: instruction-only from a checkout

```bash
cp AGENTS.md ~/your-project/AGENTS.md    # Grok reads AGENTS.md natively
```

No plugin, no hook injection: the anchor file is the enforcement.

## Platform notes

- **Grok hooks cannot inject instructions**: unlike ZCode or Claude Code,
  there is no SessionStart context injection. Do not rely on hook-based
  drift guards here; the AGENTS.md anchor plus skill descriptions carry the
  rules. This is a verified platform limit, documented by ponytail too.
- Grok's default voice is casual and chatty: token-discipline `full` is the
  sweet spot; `ultra` can drop nuance Grok treats as optional. Keep the
  never-compress list (code, paths, errors, negations) pinned.
- Grok leans on world knowledge over repo reality: anti-hallucination's
  read-before-write rule leads. Every claim about the repo comes from a file
  read this session.
- code-commenting matters extra: Grok slips em dashes and banner comments in
  when unprompted; the every-turn reminder other hosts get does not exist
  here, so check each generation.

## Engine (osa)

The map engine ships bundled as `osa.pyz` inside the skills, and runs as
`python3 -m osa` from a checkout. Since Grok hooks cannot inject and cannot
auto-run it, build and refresh the map manually:

```bash
python3 -m osa index .          # or: python3 <skills>/one-skill-army/osa.pyz index .
python3 -m osa context <term>   # read .osa/context.md first, then query
python3 -m osa fresh --auto     # after edits
```

## Skills (18, routed by the orchestrator)

Ten core disciplines plus `input-discipline`, `army-commit`, `osa-map`, and the
process skills `writing-plans`, `subagent-driven-development`, `code-review`,
`using-git-worktrees`.

## Defaults

- token-discipline: `full`
- anti-hallucination: strict, repo-grounded
- git-safety: always on
- memory: `.osa/memory/` shared with every other host
