---
name: code-review
description: >
  Request review when work is complete and receive review with rigor. Use
  before merging or when handing work off (requesting), and when acting on
  review feedback (receiving), so quality is checked against requirements and
  feedback is verified rather than blindly applied.
---

# Code Review

Two mindsets, one skill: asking for a review honestly, and receiving one
without either rubber-stamping or blind compliance.

## When to Use

- Requesting: a task is done, a major feature landed, or before a merge.
- Receiving: whenever review feedback arrives, before you implement it.

## Requesting a Review

1. **State what was asked** and how the change meets it, point by point.
2. **Show the evidence**: the diff, the tests that pass, the command output. Do
   not summarize results you have not run (see verification-before-completion).
3. **Name the risks**: what you are unsure about, what you did not test, what
   you deferred (with `osa:` markers where relevant).
4. **Scope the ask**: point the reviewer at the parts that most need eyes.

## Receiving a Review

1. **Understand before agreeing**: restate each point in your own words. If it
   is unclear or seems wrong, ask; do not perform agreement you do not have.
2. **Verify the claim**: check the code or the docs. A reviewer can be wrong;
   confirm the issue is real before you change anything.
3. **Then act**: fix real issues with a test that reproduces them where it is a
   bug. Push back, with evidence, on points that do not hold.
4. **Never comply blindly** and never dismiss reflexively. Technical rigor, not
   politeness theater, decides.

## Red Flags

| Thought | Reality |
|---|---|
| "The reviewer said so, I will just change it" | Verify the claim first; reviewers err too. |
| "Looks good to me" with no diff read | Read the diff. Approval without reading is not review. |
| "I will say it passes" without running it | Run it. Claims are not evidence. |

## Boundaries

- Never enable or invoke an automated AI code reviewer (see git-safety); this
  skill is human-grade review, not a bot handoff.
- Requesting review does not authorize the merge; merging still needs explicit
  approval (see git-safety).
