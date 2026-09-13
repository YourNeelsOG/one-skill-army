---
name: code-commenting
description: >
  Use when writing or editing ANY code, commit message, or docstring. No em
  dashes in code, no ===== banner comments, and structural comments that let
  the next developer understand what each function, engine, and block of
  logic does.
---

# Code Commenting

Code is read by the next person who touches the repo. Comments exist for
them, not for you.

## The Iron Law

```
NO EM DASHES ANYWHERE. NO BANNER COMMENTS. EVERY NON-OBVIOUS FUNCTION EXPLAINS ITSELF.
```

## Hard bans

1. **No em dashes, anywhere, in anything you write.** Code, comments,
   strings, docstrings, commit messages, docs, AND chat replies. Use a
   comma, colon, period, or hyphen.
   - BAD:  `// Fetches users — retries on 429`
   - GOOD: `// Fetches users. Retries on 429.`
   - Also BAD in chat: "one-skill-army — orchestrator, always on"
   - Also GOOD in chat: "one-skill-army: orchestrator, always on"
   Em dashes are non-ASCII, break some tooling/fonts, and are the classic
   AI-generated-prose marker. Strip them on sight, including in existing
   lines you touch and in your own prose.
2. **No banner comments.** Never `// =====`, `// ------`, `// ******`,
   `# --- SECTION ---`, `// <<< HELPERS >>>`.
   - BAD:  `// ===================== HELPERS =====================`
   - GOOD: delete the banner. If a file genuinely needs sections that big,
     split the file.

## Structural comments (required)

Write comments that let someone unfamiliar with the codebase navigate it:

- **Module/file top:** one short block saying what this file is and its role
  in the system. "Payment retry engine. Called by the webhook handler; owns
  all backoff logic."
- **Non-obvious functions:** above the function, what it does and, when it
  matters, why it exists and what it expects. Explain intent and
  constraints, not a line-by-line translation of the code.
- **Tricky logic:** every algorithm, regex, bit manipulation, workaround, or
  timing hack gets a comment explaining the WHY, including the failure mode
  it guards against.
- **Public surface:** exported functions, API handlers, and engine entry
  points always get at least a one-line purpose comment, even when the name
  is good.

Minimal-code interaction: these comments are the "one runnable check"
equivalent for readability. The ladder removes CODE, never the comments that
explain the code that remains. Fewer lines and no explanation is how the
next 3am page happens.

## Style

- Match the file's existing comment language and tone.
- Keep comments with the code they describe.
- Never comment out code "just in case". Delete it; git remembers.
- `TODO(name):` only with context on how to resolve it.
- Deliberate shortcuts get `osa:` markers (see minimal-code), not vague
  TODOs.

## Example

```ts
// Payment retry engine. Owns backoff for failed charges.
// Partial failure here means money moved partially, so never retry blind.

// Charges a card once with idempotency protection.
// Returns the provider result; throws only on network failure.
// Provider declines are returned, not thrown, so callers can log them.
async function chargeOnce(orderId: string, token: string) { ... }
```

## Rationalizations

| Excuse | Reality |
|--------|----------|
| "The code is self-documenting" | Good names help. They don't explain WHY, constraints, or failure modes. |
| "Comments rot and lie" | Bad comments rot. No comments leave nothing to rot AND nothing to learn. |
| "Git blame tells the story" | Git blame tells who and when, never why the constraint exists. |
| "It's a quick script" | Quick scripts become load-bearing. The comment takes 15 seconds. |
| "Banners help me navigate" | Banners mean the file is too big. Split it. |

## Boundaries

The em-dash ban applies to EVERY output channel: source code, comments,
docstrings, commit messages, docs, config, and chat replies. The banner
ban and structural-comment rules apply to code and docs only; chat prose
structure is token-discipline territory. "stop code-commenting" / "normal
mode": revert.
