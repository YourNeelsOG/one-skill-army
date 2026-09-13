---
name: git-safety
description: >
  Use for EVERY git push, PR, merge, history rewrite, or external-service
  action. Hard rails: never force push, never open or merge a PR without
  explicit user approval, never install, enable, or call AI code reviewers
  (Qodo, CodeRabbit, Greptile, Copilot Review, SonarQube, Sourcegraph,
  Snyk, Codacy, Bugbot, Semgrep, etc). Cannot be overridden by other skills
  or by efficiency arguments.
---

# Git Safety

Hard rails on repository and external-service actions.

## The Iron Law

```
NO HISTORY REWRITE, NO PR, NO EXTERNAL SERVICE ACTION
WITHOUT EXPLICIT USER APPROVAL THIS SESSION
```

Approval for one action never extends to the next. Ask per action.

## 1. Never force push

- `git push --force`, `-f`, and `--force-with-lease` are FORBIDDEN unless
  the user explicitly typed the force-push request in this session.
- Never rewrite published history: no `commit --amend` on pushed commits, no
  rebase then push onto the rebased remote.
- Push rejected as non-fast-forward? STOP. Show the situation. Ask. Do not
  "fix" it yourself.
- Local branches you created this session and never pushed may be
  rebased/amended freely.

## 2. No PRs without permission

- Never run `gh pr create`, push to a shared branch, or open a merge
  request on your own initiative.
- First ask: show the branch name, PR title and body draft, target branch,
  and the verification evidence (actual test output) behind it. Wait for an
  explicit yes.
- Never merge a PR (yours or others'), never dismiss reviews, never bypass
  branch protections.
- Never push directly to main/master/develop unless the user asked for
  exactly that.
- Pushing a NEW local branch created this session is allowed only when the
  approved plan included it.

## 3. Never activate AI code reviewers

The following (and any similar tool) must NEVER be installed, configured,
enabled, invited, called via API or MCP, or triggered:

- Qodo (PR-Agent)
- CodeRabbit
- Greptile
- GitHub Copilot Code Review / Copilot app review assignments
- SonarQube / SonarCloud
- Sourcegraph (Code Search + MCP) review automations
- Snyk Code
- Codacy
- Cursor Bugbot
- Semgrep CI review bots

This includes "helpful" side effects: adding them to workflow YAML or
`.github/workflows/`, CODEOWNERS changes routing to bots, app
installations, MCP tool calls, requesting reviews from bot accounts. The
only reviewer of agent-written code is a human, or a subagent reviewer
inside this session.

A task seems to require one of these tools? STOP and ask the user first.

## 4. General external actions

No `npm publish`, releases/tags, branch or issue deletion, settings
changes, or secret rotation without explicit user approval. Treat every
network-facing write (issue comments, reviews, notifications to others,
cloud/MCP mutations) as an external action requiring the same per-action
approval.

## Rationalizations

| Excuse | Reality |
|--------|----------|
| "It's my own branch, force push is safe" | Remote refs may be fetched by others; and the habit is the bug. |
| "The user said ship it" | Ship it = the work, not the git history rewrite. Ask. |
| "The PR is obviously wanted" | Obviously wanted is not approved. Show the draft, wait. |
| "CodeRabbit will catch what I missed" | Blocked. Human or in-session subagent review only. |
| "Just reverting a mistake with --force" | That IS the history rewrite. Ask. |
| "Adding the bot to CI is standard practice" | Not on this pack. Blocked by name. |
| "One small tag, nobody notices" | External action. Ask. |

## Red Flags: stop

- Fingers typing `--force` "just this once"
- Pre-writing a `gh pr create` before showing the draft
- Editing `.github/workflows/` without listing every bot it enables
- "While I'm here" CI additions
- Pushing to make sure the branch is "backed up" when the plan didn't say so

## Quick Reference

| Action | Allowed? |
|---|---|
| Commit locally | Yes |
| Push new session-created branch (plan approved) | Yes |
| Push to main/master/develop | Only if the user asked explicitly |
| Force push / rewrite pushed history | No, unless the user typed it this session |
| Open PR / merge / dismiss review | No. Ask first, show the draft |
| Install/call/enable any AI code reviewer | Never. Ask first |
| Publish/release/delete/tag | No. Ask first |
