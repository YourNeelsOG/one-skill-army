---
name: no-comments
description: "Audit scoped comments for stale narration and banners while preserving OSA module purpose, exported-function, tricky-logic, legal, and constraint comments."
---

# No comments: OSA comment audit


## OSA execution contract

Read [portable runtime and policy](../poteto-mode/references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.

Remove comments that distract or lie while preserving OSA's required structural explanations. The inherited command name is compatibility only; it does not authorize wholesale deletion.

## Scope

Use caller-named files or diff. Otherwise inspect the actual working diff against the discovered base branch. Read nearby implementations and callers before judging a comment.

## Steps

1. Give an available in-session reviewer the bundled [comment-reviewer prompt](references/comment-reviewer.md), scope, and project rules. Without delegation, perform that review as a separate serial phase. No named Comment Sicko registration or external reviewer service is required.
2. Read every proposed change. Keep module purpose blocks, purpose comments on exported and non-obvious functions, tricky-logic WHY comments, legal notices, public contracts, issue links, and real constraints. Reject scope escapes or deleting explanations merely because behavior is surprising. Ambiguity means investigate with **how** or **why**, then preserve the constraint until evidence resolves it.
3. Remove only confirmed stale narration, commented-out code, duplicates, and banner comments. Present the cleanup design before edits if the task lacks approval. A comment-only cleanup needs reference and diff checks rather than invented production behavior tests.
4. Treat suppression or workaround findings as code-review findings, never automatic removal. Read the actual lint rule and prove the claimed behavior. Propose the smallest scoped root-cause change. If production code changes, obtain design approval and apply **tdd** before implementation. If shape changes, use **architect** first.
5. For constraint comments, propose a type, runtime guard, regression test, or ordinary lint check that enforces the same constraint. Wait for design approval before adding it. Delete a comment only when the replacement fully covers it and structural-comment requirements still hold. Out-of-scope constraints remain intact and are reported.
6. Inspect the final diff, rerun relevant checks, and report deletion count, preserved explanations, proven code findings, approved encodings, and open work. A reviewer report with invented findings is rejected and rerun once; a second invalid report becomes an explicit coverage gap.
