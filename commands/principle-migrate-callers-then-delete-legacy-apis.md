---
description: "Apply when introducing a new internal API while old callers still exist. Migrate callers and delete the old API in the same wave instead of preserving compatibility layers."
---

Read the installed [principle-migrate-callers-then-delete-legacy-apis skill](../skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) in full,
then apply its workflow to `$ARGUMENTS`. Resolve references relative to that
skill directory, including when installed outside this checkout.

OSA rules take precedence: approved design before implementation, mandatory
TDD, structural comments, and explicit per-action authorization for Git and
external writes. Use only available host tools and models. If the skill cannot
be found, report the missing installation rather than inventing its workflow.
