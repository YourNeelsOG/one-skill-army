---
description: "Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect."
---

Read the installed [reflect skill](../skills/reflect/SKILL.md) in full,
then apply its workflow to `$ARGUMENTS`. Resolve references relative to that
skill directory, including when installed outside this checkout.

OSA rules take precedence: approved design before implementation, mandatory
TDD, structural comments, and explicit per-action authorization for Git and
external writes. Use only available host tools and models. If the skill cannot
be found, report the missing installation rather than inventing its workflow.
