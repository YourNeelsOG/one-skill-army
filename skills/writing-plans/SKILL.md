---
name: writing-plans
description: >
  Turn an approved design into a concrete, step-by-step implementation plan
  before touching code. Use after brainstorming or a design is approved, for
  any multi-step task, so work proceeds in reviewable increments instead of one
  large uncontrolled change.
---

# Writing Plans

A plan is the bridge between an approved design and the first line of code. It
exists so the work can be executed in small, verifiable steps and reviewed at
each boundary, not audited after the fact.

## When to Use

- After a design or spec is approved and the task needs more than one edit.
- Before starting any architectural task.
- Skip for a spike or a single-line fix; those do not earn a plan document.

## The Plan

Write the plan to `docs/plans/YYYY-MM-DD-<topic>-plan.md` and keep it in sync
as reality changes. Each step is:

1. **Goal**: one sentence on what this step delivers.
2. **Change**: the files touched and the concrete edit.
3. **Test**: the failing test that proves the step (TDD), or the command that
   verifies it.
4. **Done when**: the observable condition that closes the step.

Order steps so each one leaves the tree green and shippable. Put the riskiest
unknowns first so a wrong assumption is caught cheaply, not after ten steps
depend on it.

## Rules

- One behavior per step. If a step needs the word "and", split it.
- Every step names its verification up front; a step with no way to prove it is
  not ready to execute.
- The plan is a living document: when a step turns out wrong, fix the plan
  before writing more code, never silently diverge.
- Reference the design; do not restate it. The plan is the how, not the why.

## Red Flags

| Thought | Reality |
|---|---|
| "I will just start and figure out the steps" | Unplanned multi-step work sprawls. Write the steps first. |
| "The plan is obvious, no need to write it" | Then it takes two minutes to write and stays a reference. |
| "I will keep the plan in my head" | The next session, or the next model, cannot read your head. |

## Boundaries

- A plan is not a design: get the design approved first (see workflow).
- A plan is not implementation: no production code until a step's failing test
  exists (see test-driven-development).
