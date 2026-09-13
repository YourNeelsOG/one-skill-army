#!/usr/bin/env bash
# One Skill Army git-hook installer: wire the pack's commit guards into a
# project. Run this INSIDE the target project:
#   bash /path/to/one-skill-army/scripts/install-git-hooks.sh
# Copies hooks/git/{pre-commit,commit-msg} into <project>/.githooks/ and
# points core.hooksPath there. A project-local copy survives pack
# reinstalls and moves. Idempotent: safe to re-run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACK_HOOKS="$(cd "${SCRIPT_DIR}/.." && pwd)/hooks/git"

if [ ! -d "$PACK_HOOKS" ]; then
  echo "install-git-hooks: pack hooks not found at ${PACK_HOOKS}" >&2
  exit 1
fi
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "install-git-hooks: $(pwd) is not inside a git work tree" >&2
  exit 1
fi

mkdir -p .githooks
cp "${PACK_HOOKS}/pre-commit" "${PACK_HOOKS}/commit-msg" .githooks/
chmod +x .githooks/pre-commit .githooks/commit-msg
git config core.hooksPath .githooks

echo "install-git-hooks: installed .githooks/{pre-commit,commit-msg}"
echo "install-git-hooks: core.hooksPath=$(git config core.hooksPath)"
