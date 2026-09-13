---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code. Enforces the RED-GREEN-REFACTOR cycle with mandatory failure verification.
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** if you didn't watch the test fail, you don't know if it
tests the right thing.

**Violating the letter of the rules is violating the spirit of the rules.**

## When to Use

**Always:** new features, bug fixes, refactoring, behavior changes.

**Exceptions (ask your human partner):** throwaway prototypes, generated
code, configuration files.

Thinking "skip TDD just this once"? Stop. That's rationalization.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over. No exceptions:

- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete

Implement fresh from tests. Period.

## Red-Green-Refactor

### RED: write one failing test

One minimal test showing what should happen. Clear name. Tests real
behavior, not mocks (mocks only when unavoidable).

<Good>
```typescript
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };

  const result = await retryOperation(operation);

  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```
Clear name, tests real behavior, one thing
</Good>

<Bad>
```typescript
test('retry works', async () => {
  const mock = jest.fn()
    .mockRejectedValueOnce(new Error())
    .mockRejectedValueOnce(new Error())
    .mockResolvedValueOnce('success');
  await retryOperation(mock);
  expect(mock).toHaveBeenCalledTimes(3);
});
```
Vague name, tests the mock, not the code
</Bad>

### Verify RED (mandatory, never skip)

Run the test. Confirm:
- It fails (not errors). Errors? Fix the error, re-run until it fails correctly.
- The failure message is the expected one.
- It fails because the feature is missing, not a typo.
- It passes? You're testing existing behavior. Fix the test.

### GREEN: write minimal code

The simplest code that passes the test. Don't add features, refactor other
code, or "improve" beyond the test. Over-engineered GREEN (option objects,
strategies, config for one caller) violates minimal-code too.

### Verify GREEN (mandatory)

Run the test. Confirm it passes, other tests still pass, output pristine
(no errors, warnings). Test fails? Fix the code, not the test. Other tests
fail? Fix now.

### REFACTOR

After green only: remove duplication, improve names, extract helpers.
Stay green. Don't add behavior.

### Repeat

Next failing test for the next piece of behavior.

## Rationalizations

| Excuse | Reality |
|--------|----------|
| "Too simple to test" | Simple code breaks. The test takes 30 seconds. |
| "I'll test after" | Tests written after pass immediately, which proves nothing. You never watched it fail, so you never proved it can catch the bug. |
| "Tests after achieve the same goals" | Tests-after answer "what does this do?"; tests-first answer "what should this do?" Tests-after verify the cases you remembered, not the ones you'd have discovered. |
| "Already manually tested" | "Worked when I tried it" is not comprehensive and can't re-run. |
| "Deleting X hours of work is wasteful" | Sunk cost. Keeping code you can't trust is the waste. |
| "Keep the code as reference" | You'll adapt it. That's testing after. Delete means delete. |
| "Need to explore first" | Fine. Throw the exploration away, then start TDD. |
| "Test is hard = design is unclear" | Listen to the test. Hard to test = hard to use. |
| "TDD will slow me down" | TDD IS the pragmatic path: catches bugs before commit, enables fearless refactoring. Shortcuts mean debugging in production. |
| "Existing code has no tests" | You're improving it. Add tests for what you touch. |

## Red Flags: stop and start over

- Code before test
- Test passes immediately
- Can't explain why the test failed
- Tests added "later"
- "Just this once", "it's about spirit not ritual", "this is different because..."

**All of these mean: delete the code. Start over with TDD.**

## Bug Fix Pattern

Bug found? Write a failing test reproducing it first. The test proves the
fix and prevents regression. Never fix bugs without a test.

Full proof of a regression test: write, run (pass is WRONG here, revert the
fix and watch it fail, restore, watch it pass). If reverting the fix doesn't
fail the test, the test tests nothing.

## Verification Checklist

Before marking complete:
- [ ] Every new function/method has a test
- [ ] Watched each test fail first, for the expected reason
- [ ] Wrote minimal code to pass
- [ ] All tests pass, output pristine
- [ ] Real code, mocks only when unavoidable
- [ ] Edge cases and errors covered

Can't check every box? You skipped TDD. Start over.

## Final Rule

```
Production code -> test exists and failed first
Otherwise        -> not TDD
```

No exceptions without your human partner's permission.
