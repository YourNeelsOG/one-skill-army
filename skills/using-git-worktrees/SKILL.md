---
name: using-git-worktrees
description: >
  Isolate feature work in a separate git worktree before risky or parallel
  changes. Use when starting work that should not disturb the current
  checkout, or when running several independent efforts at once, so the main
  working tree stays clean and each effort has its own space.
---

# Using Git Worktrees

A worktree gives a branch its own directory on disk, so you can build, test,
and even run agents on isolated copies without stashing or clobbering the main
checkout.

## When to Use

- Starting feature work that needs isolation from the current workspace.
- Before executing an implementation plan, so a failed attempt is thrown away
  by deleting a directory, not by unwinding commits.
- Running two or more independent efforts in parallel.
- Skip for a quick edit on the current branch; a worktree is overhead there.

## The Flow

1. **Create**: `git worktree add ../<repo>-<branch> -b <branch>` makes a new
   directory on a new branch.
2. **Work there**: build, test, and edit inside that directory; the main
   checkout is untouched.
3. **Integrate**: when the work is done and verified, merge or open a PR from
   the branch (merging and PRs still need approval; see git-safety).
4. **Remove**: `git worktree remove ../<repo>-<branch>` when finished; delete
   the branch if it was a dead end.

## Rules

- One worktree per branch; git refuses to check out the same branch twice.
- Keep worktrees outside the main tree (a sibling directory), so tooling does
  not scan them as project files.
- Clean up finished worktrees; stale ones confuse the next session.
- If native worktree support is unavailable, fall back to a separate clone,
  but keep the same isolate-then-integrate discipline.

## Red Flags

| Thought | Reality |
|---|---|
| "I will just stash and switch branches" | Stashing is fragile for long work; a worktree is cleaner. |
| "I will work on the risky thing in the main tree" | Isolate it; a bad attempt should be a directory you delete. |
| "I left five old worktrees around" | Remove them; stale trees mislead the next session. |

## Boundaries

- A worktree isolates work; it does not authorize integration. Merge and PR
  gates still hold (see git-safety).
