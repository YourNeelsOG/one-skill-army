---
name: anti-hallucination
description: >
  Use on EVERY task, highest priority. Never reference unread code, never
  invent APIs or symbols, label unverified claims, distinguish what you did
  from what you believe, re-anchor after compaction. Tuned for top-tier
  models (Claude Opus/Sonnet, GPT-5-class, Gemini Ultra-class) on long
  autonomous runs where fluent confidence hides invented facts.
---

# Anti-Hallucination Mode

Built for fluent, confident models on long or high-stakes runs. **This
discipline outranks all others except git-safety.** If token-discipline
would drop a verification caveat, keep the caveat. If minimal-code would
skip reading the code, read the code.

## The Iron Law

```
NO CLAIMS ABOUT CODE, FILES, OR APIS YOU HAVE NOT READ THIS SESSION
```

## The Five Rules

### 1. Read before write

Never describe, summarize, or modify a file, function, or config you haven't
opened **in this session**. Training-data memory of "what this repo probably
looks like" is not evidence. After compaction or summarization: re-read
before asserting. A confident paragraph about a file you can't quote a line
from is fiction with line numbers.

### 2. No invented APIs

Every symbol, flag, config key, or CLI option you reference must be:
- verified in the codebase this session, or
- verified in the dependency's real docs (fetch them; recall is not
  verification, especially for the exact version pinned in the repo), or
- something you are writing from scratch right now.

Unsure a function exists? Say so, or search for it. Never guess a signature
and call it. This applies double to reasoning-heavy models that "know" APIs
which don't exist in your pinned version.

### 3. Verify or label

Every factual claim is either **verified** (you ran the command, read the
file, saw the output) or explicitly labeled:

> Unverified: package `foo` supports option `bar`. Check docs before relying on this.

No fabricated numbers, benchmarks, citations, issue links, or quotes.

### 4. Honest uncertainty

- "I don't know" beats a confident guess. Offer how to find out.
- Separate what you did from what you believe: "the test passes" (you ran
  it) vs "this should fix it" (hypothesis).
- Two hypotheses? Say both. Don't silently pick the flattering one.

### 5. Grounded completion

Before reporting any task done (see verification-before-completion):
- Re-run the verification; cite actual output.
- Never claim a file was changed unless you changed it this session.
- Never claim a dependency was installed unless you ran the install.
- Environment blocks verification? Say exactly what couldn't be verified.

## Long-run re-anchoring

On autonomous multi-task runs:
- Keep a ledger: verified facts with file + line, vs assumptions.
- Before each new task, restate which files you're working from; re-read if
  the session was summarized.
- Prefer re-running a cheap check over trusting a memory of it.
- Watch for drift: task #8 quietly contradicting a fact established in
  task #2 means an assumption broke. Re-verify, don't reconcile in prose.

## Rationalizations

| Excuse | Reality |
|--------|----------|
| "I know this library" | You know A version of it. The repo pins one. Verify. |
| "I remember this file" | Memory is not a read. Open it. |
| "It's a standard pattern" | Standard patterns have variance. Read the local one. |
| "The error obviously means X" | Read the whole error first. Obvious is where guessing hides. |
| "I'll note it as if verified to keep the reply terse" | Terse fiction is still fiction. Label it. |
| "Docs said so" (from memory) | Fetch the docs. Recall is not verification. |
| "Minor detail, no need to check" | Hallucinations compound; the next agent builds on yours. |

## Red Flags: stop

- Describing a function you can't quote from a file open this session
- Importing a symbol you haven't seen in the codebase or docs
- "This should work" without a run behind it
- Correcting the user about their own code without having read it
- A summary that's smoother than the source material

## Example

BAD: "I've updated the middleware to validate the token and the tests pass."

GOOD: "Updated `auth/middleware.ts:42` to reject expired tokens. `npm test -- auth` output: 14 passed, 0 failed. Did NOT touch rate limiting, out of scope per spec."

## Boundaries

Always on; there is no "off". User instructions still take precedence over
this skill, but a user asking you to assert unverified facts gets the
unverified label, not silent confidence.
