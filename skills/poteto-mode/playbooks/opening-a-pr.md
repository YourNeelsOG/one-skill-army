# Opening a PR

## OSA execution contract

Read [portable runtime and policy](../references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.



Prepare a concrete, verified PR draft. Running this playbook does not authorize opening, editing, pushing, merging, retargeting, or marking a PR ready.

1. **Protect the working tree.** Read `git status`, the actual base branch, and project Git rules. Preserve unrelated edits. Use an isolated worktree when writers would collide. Never reset or discard someone else's work. Never rewrite pushed history to make the presentation cleaner.
2. **Verify the change.** Inspect the final diff and run relevant checks. Production changes need observed RED then GREEN. Apply **unslop** to prose, **no-comments** as an OSA comment audit, and **interrogate** when warranted using only in-session tools.
3. **Shape the local delivery.** Keep units small and reviewable. Stage named files deliberately. Never stage secrets, environment files, or database dumps. Run hooks without bypass. Follow repository commit conventions and the user's preferences, not an imposed Conventional Commits format. Commit only within authorization.
4. **Write the draft.** Lead with the concrete problem and resulting behavior. Use a before/after example when helpful. Explain the chosen approach only when it helps review. Give fresh verification evidence and material limits. Keep one primary measurement in the body and link methodology only if the linked artifact is accessible. No AI tool mentions, generated-with text, or attribution trailers in commit messages or PR text.
5. **Resolve the actual forge.** Inspect available authenticated PR tools or the installed `gh` interface. Use the host's PR tool when its documented lifecycle requires it. Do not assume an Origin CLI exists merely because Git has a remote named origin. Read schemas or help before using any create or edit command.
6. **Present the action.** Show target repository, branch, base, title, complete draft body, chosen draft/ready status, and verification evidence. Obtain explicit approval for PR creation. A previous push approval or technical verdict does not approve creation. If push is needed, obtain approval for that action too, respecting protected branches.
7. **Perform only the approved action.** Use a structured argument or exact body file. Re-read actual PR state and return its real URL. Any subsequent retarget, message, review dismissal, ready transition, merge, or auto-merge is a separate action gate.
8. **Handle stacks carefully.** Describe dependency order and proposed bases in the draft. Keep a single topology owner. For published branches, absorb drift with a safe merge or create a replacement branch; never rebase pushed history. No force-push exception is inferred from stack ownership.

Opening a PR does not start a babysit or authorize landing. Route status requests to Babysit and a requested merge to Shipping, preserving its per-action approval.

**Reply:** the draft and verification while approval is pending, or the actual approved action and re-read PR URL/state after completion. State remaining independent gates.
