# Autopilot-stack

## OSA execution contract

Read [portable runtime and policy](../references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.



Build and verify dependent units, then present one ordered reviewable chain. The operator lands the chain through separately approved actions. A stack never authorizes rewriting published history.

1. **Frame and approve.** Name units, dependency order, file boundaries, actual base branch, acceptance checks, and human review gates. Execution begins only within an approved design.
2. **Run owners.** Use Autopilot-full's scoped owner, RED/GREEN, audit-trail, and fresh-review workflow. Independent units can build in isolated worktrees within actual concurrency limits. Without delegation, retain the same owner records and execute serially.
3. **Audit real progress.** Reconcile artifacts, exact heads, worker terminal states, and verifier receipts at bounded host-supported checkpoints. Never claim an unavailable background loop. Hold immediately on user stop.
4. **Verify every round.** Record code-ready and STACK-READY heads. Run gates, load-bearing real behavior, trunk comparison where meaningful, and focused diff reviews. No unit enters the reviewed chain with missing or failed required evidence.
5. **Use one topology owner.** Record the intended parent for each unit. Unpublished branches may be arranged locally without colliding with unrelated work. Published branches absorb drift through merges or replacements, never history rewrites. Obtain explicit approval before each push, PR creation, or base retarget. Keep exact draft content and action targets reviewable.
6. **Reconcile drift.** Read current trunk and parents before delivery. Delegate conflicts to the slice owner, inspect its diff, and freshly verify changed patches. Patch identity can preserve some artifact evidence under Shipping's rule, but mergeability and checks run fresh. Never force-push to repair a stack.
7. **Deliver, do not land.** Present the actual verified chain or local branch plan, root and tip, head/base identities, dependencies, verdicts, and remaining gates. No owner merges or arms auto-merge. Opening a PR and Shipping retain distinct per-action approvals.

Choose Autopilot-full for independent items whose merge actions will be separately approved. Choose Autopilot-stack for dependent items or review before landing.

**Reply:** chain order, actual links when available, one verdict per unit, current heads and bases, exclusions, pending approvals, and trail path.
