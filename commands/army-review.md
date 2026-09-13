---
description: "Review the current diff: over-engineering, hallucinated symbols, safety regressions, verbosity. One line per finding."
argument-hint: "[optional: files or commit range]"
---

Review the diff for unnecessary complexity, invented symbols, and safety
regressions. The diff's best outcome is getting shorter.

Scope: $ARGUMENTS (empty = current uncommitted diff; a commit range or file
paths limit the review to that scope).

Three passes, one report.

## Pass 1: Over-engineering (minimal-code)

Format: `L<line>: <tag> <what>. <replacement>.` (prefix `<file>:` on
multi-file diffs). Tags:

- `delete:` dead code, unused flexibility, speculative feature. Replacement: nothing.
- `stdlib:` hand-rolled thing the stdlib ships. Name the function.
- `native:` dependency or code doing what the platform already does. Name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
- `shrink:` same logic, fewer lines. Show the shorter form.

Examples:
- `L12-38: stdlib: 27-line validator class. "@" in email, 1 line; real validation is the confirmation mail.`
- `L4: native: moment.js imported for one format call. Intl.DateTimeFormat, 0 deps.`
- `L52-71: delete: retry wrapper around an idempotent local call. Nothing replaces it.`

## Pass 2: Hallucinated symbols (anti-hallucination)

Every referenced function/type/config must exist in the codebase or verified
docs. Check imports resolve. Flag anything you cannot verify, one line each:

- `L17: unverified: `fetchRetry` imported but not defined in this repo or its deps. Check.`
- `README.md:L30: ghost: references `src/engine.ts`, file does not exist.`

## Pass 3: Safety regressions (never cut)

- `L88: safety: input validation removed from the trust boundary. Revert.`
- `L12: a11y: label dropped from the date input. Restore.`

Em dashes or `====` banners introduced? Flag with `style:`.

## Scoring

End with: `net: -<N> lines possible.` and `findings: <n>`. Nothing to cut and
nothing wrong? Say `Lean already. Ship.` and stop. Does not apply fixes,
only lists them.
