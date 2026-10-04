---
description: "Build an approved UI and secure local bridge to a verified bot webhook, with provider discovery, safe credential entry, local tests, and separately approved remote access."
---

Read the installed [make-bot-ui skill](../skills/make-bot-ui/SKILL.md) in full,
then apply its workflow to `$ARGUMENTS`. Resolve references relative to that
skill directory, including when installed outside this checkout.

OSA rules take precedence: approved design before implementation, mandatory
TDD, structural comments, and explicit per-action authorization for Git and
external writes. Use only available host tools and models. If the skill cannot
be found, report the missing installation rather than inventing its workflow.
