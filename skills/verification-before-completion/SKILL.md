---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs. Requires running verification commands and confirming output before any success claim. Evidence before assertions, always.
---

# Verification Before Completion

## Overview

**Core principle:** evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot
claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: what command proves this claim?
2. RUN: the FULL command, fresh and complete
3. READ: full output, check exit code, count failures
4. VERIFY: does the output confirm the claim?
   - NO  -> state the actual status, with evidence
   - YES -> state the claim, WITH the evidence
5. ONLY THEN: make the claim

Skipping any step is lying, not verifying.
```

## Common Failures

| Claim | Requires | Not sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test of the ORIGINAL symptom passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passed once |
| Subagent completed | VCS diff shows the changes | Subagent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |
| File updated | The file was edited this session | Memory of editing it |

## Red Flags: stop

- "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!")
- About to commit/push/PR without verification
- Trusting a subagent's success report instead of its diff
- Relying on partial verification
- "Just this once"
- ANY wording implying success without having run the verification

## Rationalizations

| Excuse | Reality |
|--------|----------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence is not evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter is not a compiler |
| "Subagent said success" | Verify independently, read the diff |
| "Partial check is enough" | Partial proves nothing |
| "Different words, so the rule doesn't apply" | Spirit over letter |

## Key Patterns

Tests:
```
OK:   [run test command] [see: 34/34 pass] "All tests pass"
BAD:  "should pass now" / "looks correct"
```

Regression tests (red-green proof):
```
OK:   write -> run (fails) -> implement -> run (passes) -> revert fix -> run (MUST fail) -> restore -> run (passes)
BAD:  "I've written a regression test" (without watching it fail)
```

Subagent delegation:
```
OK:   subagent reports success -> check VCS diff -> verify changes -> report actual state
BAD:  trust the report
```

Requirements:
```
OK:   re-read the plan/spec -> checklist -> verify each item -> report gaps or completion
BAD:  "tests pass, phase complete"
```

## When to Apply

ALWAYS before:
- ANY variation of a success/completion claim
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to the next task
- After delegating to subagents

Applies to exact phrases, paraphrases, synonyms, implications, and any
communication suggesting completion or correctness.

## Honest Reporting

Verification unavailable (no test runner, sandbox blocks execution)? Say
exactly what you couldn't verify and what evidence is missing. Unverified
claims are labeled unverified (see anti-hallucination). Stop when the
acceptance proof is complete; don't add polish, cleanup, or unrelated tests
after criteria pass.
