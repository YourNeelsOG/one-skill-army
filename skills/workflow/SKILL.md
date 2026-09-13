---
name: workflow
description: >
  You MUST use this before any creative work: creating features, building
  components, adding functionality, or modifying behavior. Explores user
  intent, requirements, and design before implementation. Use when the user
  wants to build, fix, or change anything non-trivial. Trivial fixes (under
  ~10 lines, obvious cause) skip to implementation.
---

# Workflow

Turn ideas into approved designs, then implement with TDD. The ceremony
scales with the task; the approval gate never does.

<HARD-GATE>
Do NOT write any code, scaffold anything, or take any implementation action
until you have told your human partner what you intend and they have approved
it. This applies to EVERY task on EVERY path below. Presenting a design and
starting in the same breath is skipping the gate.
</HARD-GATE>

## Three Paths

Before your first question, classify the request and say the classification
out loud ("this looks bounded, so I'll present a short design here rather
than write a spec") so your human partner can override it:

- **Spike**: a feasibility question ("can we...", "quick and dirty is fine")
  whose output is an answer, not code you keep. Present the question and what
  you'll try in 2-3 sentences, get a nod, then find out as cheaply as
  correctness allows. No design doc, no spec file. Report a recommendation;
  anything built stays labeled throwaway.
- **Bounded**: a well-scoped change to a flow that already exists in this
  repo: a new flag, a small endpoint, a one-file fix. Ask the clarifying
  questions that matter, present a short design IN CHAT (a few sentences to
  a few short paragraphs), and STOP. Implementation starts only after an
  explicit yes. No spec file, no plan document.
- **Architectural**: new projects, new subsystems, changes that restructure
  how components fit or alter interfaces others depend on. Full process:
  questions one at a time, 2-3 approaches with trade-offs and a
  recommendation, design presented in sections with approval after each,
  written spec, then a task-by-task plan.

When in doubt between two paths, take the heavier one. The ratchet is
one-way: hidden complexity discovered mid-task upgrades the path. Stop, say
so, step up. Nothing downgrades mid-task.

## Red Flags

| Thought | Reality |
|---------|---------|
| "Too simple to need a design" | Simple means a short design, not no design. Two sentences in chat, then approval. |
| "I'll call it bounded and skip the spec" | Reaching for a label to skip work IS the doubt. Take the heavier path. |
| "The design is obvious, I'll start while they read it" | The gate is the approval, not the design's length. |
| "I understand this kind of app, so it's bounded" | Bounded measures the repo, not your familiarity. No existing flow = architectural. |
| "The spike works, I'll keep the code" | A spike's output is an answer. Keeping the code is a new request. |
| "It grew, but I'm almost done" | Hidden complexity upgrades the path mid-task. Stop and say so. |
| "They approved the spike, the follow-up is approved too" | Each task gets its own classification and approval. |

## Questions

One at a time. Prefer multiple choice. Focus on purpose, constraints, success
criteria. If the request describes multiple independent subsystems, flag it
immediately and decompose before refining details. A project too large for
one spec becomes sub-projects, each with its own cycle.

## Design

- Lead with your recommended approach and why. YAGNI ruthlessly; strip every
  unnecessary feature from every option.
- Scale each section to its complexity; ask after each whether it looks right.
- Cover architecture, components, data flow, error handling, testing.
- Each unit: one clear purpose, well-defined interface, understandable and
  testable alone. If a file grows large, that's a signal it does too much.
- In existing codebases: explore first, follow existing patterns, include
  targeted improvements that serve the goal. No unrelated refactoring.
- Explicit non-goals in every design. Out-of-scope is a decision, not an omission.

## Spec (architectural only)

Write the validated design to `docs/specs/YYYY-MM-DD-<topic>-design.md` and
commit. Self-review inline: placeholder scan (no TBDs), internal consistency,
scope check, ambiguity check. Fix issues and move on. Then the user review
gate:

> "Spec written and committed to `<path>`. Please review before we write the implementation plan."

Wait. Changes requested? Make them and re-review. Only then plan.

## Plan (architectural only)

Break the spec into small tasks (each minutes, not hours, of agent work).
Each task lists exact file paths, what changes, and how to verify: the
command or test that proves it. Sequence so tests come first. The plan is a
checklist; executing a task means TDD, not typing.

## Execution

- Trivial fixes: implement directly, still leave the one runnable check.
- Everything else: the test-driven-development skill, per task, strictly.
- Subagents available? One fresh subagent per task with the task text and
  file list, then review its diff with verification-before-completion before
  integration. Never trust a subagent's success report; read its diff.
- Blocked on a decision only the human can make? Ask. Don't improvise scope.

## Finish

Verification-before-completion gate, then army-review on the diff, then (only
with explicit user approval per git-safety) commit/PR. Report: what changed,
what was verified with actual command output, what was deferred (`osa:`
markers), what is unverified.

## Boundaries

User instructions (CLAUDE.md, AGENTS.md, direct requests) take precedence
over this skill. "stop workflow" / "normal mode": revert. Spike code stays
throwaway unless re-classified.
