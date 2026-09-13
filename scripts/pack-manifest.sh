#!/usr/bin/env bash
# Single source of truth for what the pack ships. Sourced by both installers
# (install.sh generic, install-zcode.sh) so the skill/command lists never drift.
#
# When you rename or drop a skill or command, MOVE it into the RETIRED_* list
# so every host's upgrade prunes the orphan instead of leaving it behind.

SKILLS=(one-skill-army memory minimal-code token-discipline workflow
        test-driven-development systematic-debugging
        verification-before-completion anti-hallucination code-commenting
        git-safety army-commit input-discipline osa-map
        writing-plans subagent-driven-development code-review
        using-git-worktrees)

COMMANDS=(army.md army-review.md army-audit.md army-debt.md army-help.md
          army-gain.md army-compress.md osa-map.md)

# Retired in past versions; pruned on every install so upgrades leave no orphan.
RETIRED_SKILLS=(graphify)
RETIRED_COMMANDS=(graphify.md)
