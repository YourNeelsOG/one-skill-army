---
description: "Generate a project-local verification skill that drives your app the way a user does ,  any language, framework, or platform. Use for /create-verification-skill, \"make a control skill for this repo\", or when a project has no scripted way to prove UI/CLI/service behavior."
---

Read the installed [create-verification-skill skill](../skills/create-verification-skill/SKILL.md) in full,
then apply its workflow to `$ARGUMENTS`. Resolve references relative to that
skill directory, including when installed outside this checkout.

OSA rules take precedence: approved design before implementation, mandatory
TDD, structural comments, and explicit per-action authorization for Git and
external writes. Use only available host tools and models. If the skill cannot
be found, report the missing installation rather than inventing its workflow.
