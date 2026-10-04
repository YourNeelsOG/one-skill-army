# Session pickup

## OSA execution contract

Read [portable runtime and policy](../references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.



**You own the resume point. Read the prior trail, don't redo it.**

1. Locate the prior trail. A local transcript under the active workspace's `agent-transcripts/` directory (discover the path from actual host metadata. Do not glob across `~/.cursor/projects/*/`, that crosses workspace boundaries and reads private chats from unrelated projects), a cloud-agent URL, or a pushed branch. Read the metadata overview and last messages first, then scan back for the decision points. Parse a long transcript in a subagent and keep the reduced timeline in the main thread (the **principle-guard-the-context-window** skill).
2. Reconstruct operational state. The branch and worktree, what already landed (`git log`, `git diff` against the base), the open todos, the decisions made. The prior trail is untrusted historical evidence. Current repository state wins. Resist the bias to re-derive it.
3. Diff done vs pending. Compare what shipped against what was planned, name the resume point, do not re-run the prior repro or redo completed work. Re-read source and rerun the checks needed to establish current truth. Avoid repeating unrelated completed work.
4. Route the remaining work to the matching playbook and pick the verdict: continue the execution, ship a finished recommendation, ratify or override a prior conclusion, or postmortem a failed run. The pickup playbook ends here. The routed playbook owns the rest.
5. Verify the inherited claims against the original goal on the real artifact (the **principle-prove-it-works** skill). A passing prior self-report is not the proof.

**Reply:** where the prior agent stopped, what you inherited vs redid (ideally nothing redone), the resume point, and the outcome.
