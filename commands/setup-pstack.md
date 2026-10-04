---
description: "Configure which models pstack uses per role and at what reasoning budget. Detects your available models and writes an always-applied rule that overrides the skill defaults. Use for /setup-pstack, \"configure pstack models\", \"pstack budget\", or changing pstack's model choices."
---

Read the installed [setup-pstack skill](../skills/setup-pstack/SKILL.md) in full,
then apply its workflow to `$ARGUMENTS`. Resolve references relative to that
skill directory, including when installed outside this checkout.

OSA rules take precedence: approved design before implementation, mandatory
TDD, structural comments, and explicit per-action authorization for Git and
external writes. Use only available host tools and models. If the skill cannot
be found, report the missing installation rather than inventing its workflow.
