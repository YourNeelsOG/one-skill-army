---
name: subagent-driven-development
description: >
  Execute independent plan steps by dispatching a fresh subagent per task and
  verifying each result against the real diff. Use when an approved plan has
  steps that do not share state, to keep the main context clean and parallelize
  safely.
---

# Subagent-Driven Development

Independent work runs better in fresh subagents: each starts with a clean
context, does one task, and reports back. The main thread stays a coordinator,
not a doer, so its context lasts and its judgment stays sharp.

## When to Use

- An approved plan has two or more steps with no shared state or ordering
  dependency.
- A task is well-bounded enough to hand off with a self-contained brief.
- Do not use for exploratory work where the shape is still unknown, or for
  steps that must run in strict sequence sharing intermediate state.

## The Loop

1. **Scope one task**: pick a step whose brief stands alone (paths, acceptance
   test, and constraints all included; the subagent cannot see this
   conversation).
2. **Dispatch a fresh subagent** per independent task. Dispatch the batch in
   one message so they run in parallel.
3. **Verify against the diff**: when a subagent reports success, read the actual
   change. A success report is a claim, not evidence (see
   verification-before-completion).
4. **Integrate**: only merge work you have verified. Re-dispatch a corrected
   brief if the result is wrong; do not fix it silently in the main thread.

## Rules

- One task per subagent brief. Bundling tasks defeats the clean-context point.
- The brief is self-contained: a subagent has none of this conversation's
  context, so paths, the failing test, and the definition of done go in the
  brief.
- Never trust a "done" without reading the diff or running the test yourself.
- Keep shared-state work on the main thread; only fan out what is truly
  independent.

## Red Flags

| Thought | Reality |
|---|---|
| "The subagent said it passed, ship it" | Read the diff. Reports are claims. |
| "I will give it the whole plan" | One task per brief; it cannot hold the rest. |
| "These steps kind of depend on each other" | Then they are not independent. Run them in sequence. |

## Boundaries

- This is execution, not planning: the plan must already exist (see
  writing-plans) and be approved.
- Verification still applies to every returned result (see
  verification-before-completion).
