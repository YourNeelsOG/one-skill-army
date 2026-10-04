---
description: "Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
---

Read the installed [swarm skill](../skills/swarm/SKILL.md) in full,
then apply its workflow to `$ARGUMENTS`. Resolve references relative to that
skill directory, including when installed outside this checkout.

OSA rules take precedence: approved design before implementation, mandatory
TDD, structural comments, and explicit per-action authorization for Git and
external writes. Use only available host tools and models. If the skill cannot
be found, report the missing installation rather than inventing its workflow.
