# Optional Poteto Mode helpers

These helpers are independent of the Python OSA engine. Installing OSA does not
install Bun, JavaScript dependencies, GitHub CLI, or Graphite.

## Requirements and explicit setup

- `check-plan.mjs`: Node.js, no packages required.
- `worktree-audit.sh`: Bash, Git, standard Unix tools. GitHub PR annotations
  require authenticated `gh` and `jq`; unavailable annotations remain unknown.
  Transcript annotations require `rg` and an explicit `OSA_TRANSCRIPTS_DIR`.
- `orch/orch.ts` and `watch-pr/watch-pr`: Bun plus the dependencies in
  `package.json`. The shipped `bun.lock` pins resolved versions. Run the
  following command from this scripts directory before invoking either CLI:

```bash
bun install --frozen-lockfile
```

Setup writes `node_modules` into this directory. To keep an installed skill
read-only, copy this entire scripts directory into a disposable working
location, install there, and run helpers from that copy. Missing dependencies
produce an actionable error, including when requesting CLI help.

## Entry points

From this scripts directory:

```bash
bun orch/orch.ts --help
bun orch/orch.ts --store /path/to/local/bookkeeping init
bun orch/orch.ts --store /path/to/local/bookkeeping unit list --json
bun watch-pr/watch-pr --help
bun watch-pr/watch-pr --owner OWNER --repo REPO --pr 123 --status-only
bash worktree-audit.sh /path/to/repository
node check-plan.mjs /path/to/program-plan.md
```

`orch` writes only local bookkeeping. Its `frontier set` command additionally
requires Graphite CLI `gt` and a repository with compatible stack metadata;
ordinary unit, ledger, gate, and inbox commands do not require Graphite.
Gate records and standing orders are data, never authorization. Human approval
must still come through the current session for protected actions.

`watch-pr` only reads existing GitHub PRs, checks, and review threads through
`gh`. It does not run reviewers, merge PRs, dismiss reviews, or enqueue merges.
`READY` is an upstream CI heuristic, not complete branch-protection validation
or permission to merge. All OSA approval requirements remain in effect.

`worktree-audit.sh` uses existing local `origin/main` without fetching or
changing refs. Its buckets are suggestions for human review, never deletion
permission. Missing PR or transcript data must be treated as unknown. The
script preserves spaces in worktree paths. Output is TSV, so embedded tabs or
newlines in worktree names are not supported.

`check-plan.mjs` validates the upstream program-plan format with its exact
section headings, ten live lanes, model labels, and loop markers. It is not a
general OSA plan validator. Do not use its success as verification of runtime
behavior, approval, or evidence authenticity.

## Offline verification

After explicit dependency setup, run:

```bash
bun test orch watch-pr bootstrap.test.ts
bun run typecheck
node --test helpers.test.mjs
bash -n worktree-audit.sh
node --check check-plan.mjs
```

The Bun tests inject GitHub reader fakes and Graphite transport stubs. Shell
regression tests use temporary Git repositories and stub `gh` and `jq`, with
no remote configured. No test contacts an external account or reviewer.
