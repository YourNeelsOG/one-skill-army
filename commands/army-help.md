---
description: "One Skill Army reference card: levels, skills, commands, config. One-shot display, changes nothing."
---

Display this reference card. One-shot: do NOT change mode, write files, or
persist anything.

## Levels

| Level | Trigger | What it does |
|-------|---------|--------------|
| **lite** | `/army lite` | Build what's asked; name the lazier alternative in one line. Prose keeps full sentences, no filler. |
| **full** | `/army full` | Default. Ladder enforced. Terse fragments. |
| **ultra** | `/army ultra` | YAGNI extremist; telegram prose; challenges requirements before building. |
| **off** | `/army off` | Normal prose, normal build style. |

Level sticks until changed or session end. The four words lite/full/ultra/off
are the only levels; anything else ("high", "max", numbers) is not a level:
list these four and ask.

## Skills (auto-trigger)

| Skill | Leads when |
|-------|------------|
| one-skill-army | Every session: routes to the rest |
| memory | Session start (recall), task end (handoff) |
| minimal-code | Any coding task: the ladder + the Two Questions |
| token-discipline | All chat replies: terse prose, never terse facts |
| input-discipline | Reads, logs, exploration: smallest read that answers; cheap subagent for broad search |
| workflow | "Let's build X": classify, design, approval gate |
| test-driven-development | Implementing: failing test first |
| systematic-debugging | Bugs, test failures, unexpected behavior |
| verification-before-completion | Before claiming done: fresh evidence |
| anti-hallucination | Always: no unread code claims, no invented APIs |
| code-commenting | Writing code: no em dashes, no banners, structural comments |
| git-safety | Git/external actions: no force push, ask-first PRs, no reviewer bots |
| writing-plans | Approved design, multi-step task: steps before code |
| subagent-driven-development | Independent plan steps: fresh subagent each, verify the diff |
| code-review | Work complete, or review feedback arrives |
| using-git-worktrees | Risky or parallel work needing isolation |
| army-commit | "write a commit" |
| osa-map | Project structure/dependency questions: query the osa map first |

## Engine (osa)

The native project-memory tool. Deterministic, zero-dependency, no LLM. Ships
bundled as `osa.pyz` inside this skill, so it runs with no install: use
`python3 <skills>/one-skill-army/osa.pyz <cmd>` (shown below as `python3 -m osa`
for a repo checkout).

| Command | Does |
|---------|------|
| `python3 -m osa index .` | Build the map: `.osa/graph.json` + `context.md` |
| `python3 -m osa context <term>` | Smallest useful slice, no repo scan |
| `python3 -m osa fresh --auto` | Re-index only changed files |
| `python3 -m osa explain <node>` | Node role: degree, community, betweenness |
| `python3 -m osa path <a> <b>` | Shortest path between two parts |
| `python3 -m osa measure` | Tokens the map saves vs reading the tree |

## Commands

| Command | Does |
|---------|------|
| /army [level] | Set intensity |
| /army-review | Diff review: delete:/stdlib:/native:/yagni:/shrink: + hallucinated symbols + safety regressions |
| /army-audit | Whole-repo version of the above, ranked biggest cut first |
| /army-debt | Harvest `osa:` shortcut markers into a ledger |
| /army-compress | Compress a memory/instruction file to terse, backup + gate |
| /army-gain | Measured-impact scoreboard (honest numbers only) |
| /osa-map [status\|update\|query] | Build, refresh, or query the osa project map |
| /army-help | This card |

## Deactivate

The user's ENTIRE message "stop" or "normal mode" deactivates the mode
levels. A phrase inside a larger request does not.

## Configure default level

Resolution: `OSA_DEFAULT_MODE` env var > `defaultMode` in `<repo>/.osa/config.json` > `full`.
`"off"` disables auto-activation; `/army` activates manually.

```json
{ "defaultMode": "lite" }
```
