#!/usr/bin/env bash
# Single source of truth for what the pack ships. Sourced by both installers
# (install.sh generic, install-zcode.sh) so the skill/command lists never drift.
#
# When you rename or drop a skill or command, MOVE it into the RETIRED_* list
# so every host's upgrade prunes the orphan instead of leaving it behind.

SKILLS=(one-skill-army memory minimal-code token-discipline workflow
        test-driven-development systematic-debugging
        verification-before-completion anti-hallucination code-commenting
        git-safety army-commit input-discipline mapit
        writing-plans subagent-driven-development code-review
        using-git-worktrees)

COMMANDS=(army.md army-review.md army-audit.md army-debt.md army-help.md
          army-gain.md army-compress.md mapit.md)

# Adapted pstack workflows, pinned source recorded beside poteto-mode.
POTETO_SKILLS=(
    architect
    arena
    automate-me
    benchmark-checklist
    blast-radius
    bro
    correct
    create-verification-skill
    figure-it-out
    how
    interrogate
    maintain-verification-skill
    make-bot-ui
    no-comments
    poteto-mode
    principle-attack-the-premise
    principle-boundary-discipline
    principle-build-the-lever
    principle-encode-lessons-in-structure
    principle-exhaust-the-design-space
    principle-experience-first
    principle-explain-the-number
    principle-fix-root-causes
    principle-foundational-thinking
    principle-guard-the-context-window
    principle-laziness-protocol
    principle-make-operations-idempotent
    principle-migrate-callers-then-delete-legacy-apis
    principle-minimize-reader-load
    principle-model-the-domain
    principle-never-block-on-the-human
    principle-outcome-oriented-execution
    principle-prove-it-works
    principle-redesign-from-first-principles
    principle-separate-before-serializing-shared-state
    principle-sequence-verifiable-units
    principle-subtract-before-you-add
    principle-test-behavior-not-implementation
    principle-type-system-discipline
    recall
    reflect
    setup-pstack
    show-me-your-work
    swarm
    tdd
    teach
    technical-writing
    typescript-best-practices
    unslop
    why
)
SKILLS+=("${POTETO_SKILLS[@]}")
for skill in "${POTETO_SKILLS[@]}"; do COMMANDS+=("$skill.md"); done

# Retired in past versions; pruned on every install so upgrades leave no orphan.
RETIRED_SKILLS=(graphify osa-map)
RETIRED_COMMANDS=(graphify.md osa-map.md)
