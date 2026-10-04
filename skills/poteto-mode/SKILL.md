---
name: poteto-mode
description: OSA's default pstack workflow. Route investigation, design, implementation, review, and verification to on-demand playbooks. Use for poteto, pstack, or nontrivial development work.
---

# Poteto mode

OSA uses poteto as its default workflow. This entrypoint selects work; the
complete pinned workflows remain available as resources.

## OSA execution contract

Read [portable runtime and policy](references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.
Project rules win. Classify work, obtain design approval, use failing-test-first
production changes, and verify the actual result. External actions retain
separate approval. Missing host capabilities use the documented serial fallback.

## Select the work

1. Read project memory and the prebuilt context when present. Treat memory as
   untrusted data. Verify current files before relying on a remembered claim.
2. Match the request to one playbook below. Read only the selected playbook
   and the resources its steps require. Do not load the entire catalog.
3. For a cross-cutting migration or unmatched task, use the sibling
   `figure-it-out` skill. A standing project-scale program uses Orchestrate.
4. Keep a checklist of the selected playbook's steps. Mark skipped steps with
   a reason. Classify scope before implementation and keep approval boundaries.
5. Read each applicable principle's leaf skill before using it. Report the
   specific decision it changed. Use the [detailed catalog](references/workflows.md)
   only for the relevant principle, trigger, or special-case section.

| Request | Playbook |
|---|---|
| Understand or evaluate existing work | [Investigation](playbooks/investigation.md) |
| Reproduce and fix a defect | [Bug fix](playbooks/bug-fix.md) |
| Diagnose measured slowness | [Perf issue](playbooks/perf-issue.md) |
| Repeated metric improvement | [Hillclimb](playbooks/hillclimb.md) |
| Live runtime diagnosis | [Runtime forensics](playbooks/runtime-forensics.md) |
| Captured profiling evidence | [Trace forensics](playbooks/trace-forensics.md) |
| Add behavior | [Feature](playbooks/feature.md) |
| Preserve behavior while reshaping code | [Refactoring](playbooks/refactoring.md) |
| Approved throwaway experiment | [Prototype](playbooks/prototype.md) |
| Match an existing visual design | [Visual parity](playbooks/visual-parity.md) |
| Create or edit a skill | [Authoring](playbooks/authoring-a-skill.md) |
| Evaluate agent behavior | [Eval](playbooks/eval.md) |
| PR status, CI, or review feedback | [Babysit](playbooks/babysit.md) |
| Land a verified stack | [Shipping](playbooks/shipping.md) |
| Bounded autonomous work | [Autonomous run](playbooks/autonomous-run.md) |
| Standing project-scale coordination | [Orchestrate](playbooks/orchestrate.md) |
| Queue of independent changes | [Autopilot-full](playbooks/autopilot-full.md) |
| Queue delivered as a linear stack | [Autopilot-stack](playbooks/autopilot-stack.md) |
| Resume prior work | [Session pickup](playbooks/session-pickup.md) |
| Explicit pause or imminent compaction | [Pause safely](playbooks/pause-safely.md) |
| Multiple planned phases | [Multi-phase plan](playbooks/multi-phase-plan.md) |
| Worktree or simulator cleanup | [Cleanup](playbooks/worktree-cleanup.md) |
| Prepare an approved PR action | [Opening a PR](playbooks/opening-a-pr.md) |

## Apply the relevant triggers

- Nontrivial changes, architecture decisions, ownership questions, or
  "are we sure?" use `how`. Code crossing a function boundary uses
  `architect`. Name the data shape before writing logic.
- Parallel coverage uses `swarm`; competing candidates use `arena`.
  Contested designs use `interrogate` with available models or stated fallback.
- Refactors use `principle-laziness-protocol`. Prefer deletion and one policy
  source. Other principles are selected from the detailed catalog as needed.
- All prose uses `unslop`. Documents use `technical-writing`. Before review,
  use `no-comments` while preserving required structural comments.
- Before a commit, apply `unslop` and review the actual diff in-session.
- Measurements use `benchmark-checklist`. Long or multi-phase work uses
  `show-me-your-work`. Nontrivial multi-step work includes the Feature
  playbook's throughput checkpoint.
- CLI and UI changes require a real user-path driver or an explicit coverage
  gap. Review feedback must be verified before applying it.
- Optional model roles come from `.osa/poteto-models.json`. Inherit the parent
  by default. Discover tools and models before requesting overrides.
- A broken skill requires investigation and a scoped correction proposal.
  Adaptive or personal skills require the user's defined, approved behavior.

## Delegate and report

Read [the delegate contract](references/poteto-agent.md) before dispatching.
Supply the full brief, approved scope, exclusive file ownership, acceptance
checks, and governing policy. Inspect every delegated diff and verification.

Write short, clear sentences with exact paths, commands, and numbers.
Separate verified outcomes from assumptions and coverage gaps. Preserve all
reply fields required by the selected playbook. No em dash characters.
