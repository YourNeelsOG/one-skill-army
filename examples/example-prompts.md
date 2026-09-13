# Example Prompts

## Minimal code in action

**Prompt:** "Add a date picker to the settings form for the user's birthday."

**Expected behavior:** agent first checks for a native option (`<input type="date">`), checks the codebase for an existing picker, and only then considers a library: with a justification per the ladder. It should NOT scaffold a `DatePickerWrapper` component with theming config for one input.

**Prompt:** "We need a deep clone of this config object."

**Expected:** `structuredClone(config)`: one line, no `lodash.clonedeep` dependency, no hand-rolled recursive clone.

## Workflow in action

**Prompt:** "Checkout is slow and users get double-charged sometimes. Fix it."

**Expected:** full workflow: brainstorm (clarify: which payment provider? when does it happen?), spec (idempotency keys on the charge endpoint, out of scope: UI changes), plan (tasks with file paths), TDD (failing test reproducing the double charge first), two-stage review.

## Token discipline in action

**Prompt:** "/army ultra: why does my list rerender on every keystroke?"

**Expected reply:** "New array in render → `map` output new refs → children re-render. Memoize list items with `React.memo`, move filter outside render. `App.tsx:31`."

## Anti-hallucination in action

**Prompt:** "Does our logging middleware retry on 429?"

**Bad:** "Yes, it retries with exponential backoff." (invented)

**Expected:** reads `middleware/logger.ts` this session, then: "Yes: `logger.ts:58`, 3 retries, 1s/2s/4s backoff, 429 only." or "No retry logic found in `logger.ts`. Unverified whether the SDK retries internally: checking its docs before relying on that."

## Memory in action

**Session start:**
> agent reads `.osa/memory/MEMORY.md` + `HANDOFF.md`, then: "Recalled: 2 decisions, 1 handoff (checkout idempotency, task 3 of 4). Continuing."

**A memory entry says "deploy script is `scripts/deploy.sh`" but the file doesn't exist:**
> BAD: runs `scripts/deploy.sh` because memory said so.
> GOOD: "Memory (2026-08-02) says `scripts/deploy.sh`, but it's not in the repo. Repo wins. Removed the stale entry; deploy now runs via `make deploy`."

**Compaction hits mid-refactor:**
> agent had written HANDOFF.md at the last green commit, re-reads it plus the three files named "In progress" after compaction, and continues instead of re-exploring.
