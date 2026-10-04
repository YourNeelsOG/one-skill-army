// Exercise portable helpers in isolated repositories without external account access.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
const script = join(dirname(fileURLToPath(import.meta.url)), 'worktree-audit.sh');

// A fake transport records calls so tests cannot contact a real remote.
function fixture(operation, prState = null) {
  const root = mkdtempSync(join(tmpdir(), 'osa-helper-'));
  const repo = join(root, 'main repo');
  const worktree = join(root, 'feature worktree');
  const bin = join(root, 'bin');
  const calls = join(root, 'calls');
  mkdirSync(repo); mkdirSync(bin); writeFileSync(calls, '');
  const git = (...args) => {
    const result = spawnSync('git', ['-C', repo, ...args], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
  };
  git('init', '--initial-branch=main'); git('config', 'user.name', 'Test');
  git('config', 'user.email', 'test@example.invalid');
  writeFileSync(join(repo, 'file'), 'initial'); git('add', '.'); git('commit', '-m', 'fixture');
  git('worktree', 'add', '-b', 'feature', worktree);
  const realGit = spawnSync('which', ['git'], { encoding: 'utf8' }).stdout.trim();
  writeFileSync(join(bin, 'git'), '#!/bin/bash\nprintf "%s\\n" "$*" >> "$OSA_TEST_CALLS"\nexec "' + realGit + '" "$@"\n', { mode: 0o755 });
  writeFileSync(join(bin, 'gh'), '#!/bin/bash\nprintf "%s\\n" "$*" >> "$OSA_TEST_CALLS"\nprintf "%s\\n" "$OSA_TEST_PRS"\n', { mode: 0o755 });
  writeFileSync(join(bin, 'jq'), '#!/usr/bin/env python3\nimport json, sys\nfor item in json.load(open(sys.argv[-1])):\n if item["headRefName"] == sys.argv[4]: print("#" + str(item["number"]) + "/" + item["state"])\n', { mode: 0o755 });
  const result = spawnSync('bash' , [script, repo], { encoding: 'utf8', env: { ...process.env, PATH: bin + ':' + process.env.PATH, OSA_TEST_CALLS: calls, OSA_TEST_PRS: JSON.stringify(prState ? [{ number: 1, state: prState, headRefName: "feature" }] : []) } });
  try { operation({ result, worktree, calls: readFileSync(calls, 'utf8') }); }
  finally { rmSync(root, { recursive: true, force: true }); }
}

test('worktree audit never fetches or mutates Git refs', () => fixture(({ result, calls }) => {
  assert.equal(result.status, 0, result.stderr);
  assert.doesNotMatch(calls, /(?:^|\n)fetch\b/);
}));

test('worktree audit preserves spaces in complete worktree paths', () => fixture(({ result, worktree }) => {
  assert.equal(result.status, 0, result.stderr);
  assert.ok(result.stdout.split('\n').some(line => line.endsWith('\t' + worktree)), result.stdout);
}));

test('closed unmerged pull requests require review before pruning', () => fixture(({ result }) => {
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /#1\/CLOSED\t-\treview\t/);
}, 'CLOSED'));
