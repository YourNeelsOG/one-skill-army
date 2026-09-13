---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes. Diagnose before editing; evidence before hypotheses.
---

# Systematic Debugging

## Overview

**Core principle:** ALWAYS find the root cause before attempting fixes.
Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Any technical issue: test failures, production bugs, unexpected behavior,
performance problems, build failures, integration issues.

**Especially when:** under time pressure (emergencies make guessing
tempting), "just one quick fix" seems obvious, you've already tried multiple
fixes, the previous fix didn't work, you don't fully understand the issue.

## The Four Phases

Complete each phase before the next.

### Phase 1: Root Cause Investigation

1. **Read error messages carefully.** Completely. They often contain the
   exact solution. Note line numbers, file paths, error codes. Quote the
   shortest decisive line, don't dump the log.
2. **Reproduce consistently.** Exact steps? Every time? Not reproducible?
   Gather more data, don't guess.
3. **Check recent changes.** Git diff, recent commits, new dependencies,
   config changes, environmental differences.
4. **Gather evidence at component boundaries** (CI -> build -> sign, API ->
   service -> DB): log what enters and exits each component, verify
   config/state propagation, run once to see WHERE it breaks, then
   investigate that component.
5. **Trace data flow backward.** Where does the bad value originate? What
   called this with it? Keep tracing up to the source. Fix at source, not
   symptom.

Stop exploration when evidence is sufficient to name the cause or the exact
blocker. Separate observed symptom from inferred cause; don't edit product
code until one credible mechanism explains the evidence.

### Phase 2: Pattern Analysis

1. Find similar working code in the same codebase.
2. Read reference implementations COMPLETELY, every line. No skimming.
3. List every difference between working and broken, however small. Don't
   assume "that can't matter".
4. Understand dependencies: components, config, environment, assumptions.

### Phase 3: Hypothesis and Testing

1. Form ONE hypothesis. State it: "X is the root cause because Y." Write it
   down. Specific, not vague.
2. Test minimally: the SMALLEST change that tests it. One variable at a
   time. Never multiple fixes at once.
3. Worked? Phase 4. Didn't? NEW hypothesis, not another fix stacked on top.
4. Don't know? Say "I don't understand X". Don't pretend. Ask, research.

### Phase 4: Implementation

1. **Create the failing test** reproducing the bug (see
   test-driven-development). MUST exist before fixing.
2. **Implement the single fix** addressing the root cause. ONE change. No
   "while I'm here" improvements, no bundled refactoring.
3. **Verify** with verification-before-completion before claiming success.
4. **Fix didn't work?** STOP. Count your attempts.
   - Fewer than 3: back to Phase 1 with the new information.
   - 3 or more: STOP and question the architecture (below). Do NOT attempt
     fix #4 without that discussion.

### 3+ fixes failed = wrong architecture, not wrong hypothesis

Signals: each fix reveals new coupling somewhere else; fixes require
"massive refactoring"; each fix creates new symptoms. Stop and ask: is this
pattern fundamentally sound? Are we sticking with it through inertia?
Discuss with your human partner before touching anything else.

## Red Flags: stop and follow the process

- "Quick fix for now, investigate later"
- "Just try changing X and see"
- "Add multiple changes, run tests"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- Proposing solutions before tracing data flow
- "One more fix attempt" (when already 2+ failed)
- Each fix revealing a new problem somewhere else

**All of these mean: STOP. Return to Phase 1.**

## Rationalizations

| Excuse | Reality |
|--------|----------|
| "Issue is simple, no process needed" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Try this first, then investigate" | The first fix sets the pattern. Do it right from the start. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms is not understanding root cause. |
| "One more attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern. |

## Quick Reference

| Phase | Key activities | Success criteria |
|-------|----------------|-------------------|
| 1. Root cause | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
| 2. Pattern | Find working examples, compare | Identify differences |
| 3. Hypothesis | One theory, test minimally | Confirmed or new hypothesis |
| 4. Implementation | Failing test, single fix, verify | Bug resolved, tests pass |

## When there is no root cause

If investigation shows the issue is truly environmental, timing-dependent,
or external: you've completed the process. Document what you investigated,
implement appropriate handling (retry, timeout, error message), add
monitoring for next time. But 95% of "no root cause" is incomplete
investigation.
