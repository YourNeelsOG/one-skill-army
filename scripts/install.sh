#!/usr/bin/env bash
# Generic One Skill Army installer/upgrader for copy-based hosts.
#
# Works for Claude Code (~/.claude), Gemini CLI (~/.gemini), the cross-tool
# ~/.agents scope, or any custom skills root. It copies the skills (including
# the bundled osa engine), the commands, prunes anything retired in a past
# version, and stamps a version receipt, so re-running it IS the upgrade.
#
# ZCode has its own installer (install-zcode.sh) because it also wires the
# SessionStart / UserPromptSubmit hooks into ~/.zcode/cli/config.json. This
# generic one does skills + commands only; on copy-based hosts the rules load
# from the skill auto-trigger and the instruction anchor (CLAUDE.md / GEMINI.md).
#
#   scripts/install.sh claude              install or upgrade under ~/.claude
#   scripts/install.sh gemini              install or upgrade under ~/.gemini
#   scripts/install.sh --dir PATH          install under a custom base dir
#   scripts/install.sh claude --doctor     show installed vs source version
#   scripts/install.sh claude --uninstall  remove skills + commands (memory kept)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=scripts/pack-manifest.sh
source "$REPO_ROOT/scripts/pack-manifest.sh"

PACK_VERSION="$( (cd "$REPO_ROOT" && python3 -m osa version) 2>/dev/null || echo unknown )"

host="${1:-}"
shift || true
case "$host" in
  claude) BASE="$HOME/.claude" ;;
  gemini) BASE="$HOME/.gemini" ;;
  agents) BASE="$HOME/.agents" ;;
  --dir)  BASE="${1:-}"; shift || true ;;
  *) echo "usage: $0 <claude|gemini|agents|--dir PATH> [--doctor|--uninstall]"; exit 2 ;;
esac
[ -n "$BASE" ] || { echo "ERROR: no target base dir"; exit 2; }

# Reject overlapping trees before any replacement can delete source skills.
python3 - "$REPO_ROOT" "$BASE" <<'PY'
import sys
from pathlib import Path
source, target = (Path(value).resolve() for value in sys.argv[1:])
if source == target or source in target.parents or target in source.parents:
    sys.exit("ERROR: install destination must not overlap the source checkout")
PY

SKILLS_DIR="$BASE/skills"
COMMANDS_DIR="$BASE/commands"
RECEIPT="$BASE/.one-skill-army-version"
action="${1:-install}"

prune_retired() {
  for s in "${RETIRED_SKILLS[@]}"; do rm -rf "$SKILLS_DIR/$s" 2>/dev/null; done
  for c in "${RETIRED_COMMANDS[@]}"; do rm -f "$COMMANDS_DIR/$c" 2>/dev/null; done
}

do_install() {
  echo "==> Installing One Skill Army -> $BASE"
  # A failed build must not install a stale engine or stamp a success receipt.
  python3 "$REPO_ROOT/scripts/build-osa.py" >/dev/null

  local prev="none"
  [ -f "$RECEIPT" ] && prev="$(cat "$RECEIPT" 2>/dev/null)"
  if [ "$prev" != "none" ] && [ "$prev" != "$PACK_VERSION" ]; then
    echo "==> Upgrading from $prev to $PACK_VERSION"
  fi

  mkdir -p "$SKILLS_DIR" "$COMMANDS_DIR"
  prune_retired

  for s in "${SKILLS[@]}"; do
    [ -d "$REPO_ROOT/skills/$s" ] || { echo "ERROR: skills/$s missing; run from the repo." >&2; exit 1; }
    rm -rf "$SKILLS_DIR/$s"
    cp -r "$REPO_ROOT/skills/$s" "$SKILLS_DIR/$s"
  done
  echo "    skills   -> $SKILLS_DIR (${#SKILLS[@]} skills, osa engine bundled)"

  for c in "${COMMANDS[@]}"; do
    [ -f "$REPO_ROOT/commands/$c" ] || { echo "ERROR: commands/$c missing." >&2; exit 1; }
    cp "$REPO_ROOT/commands/$c" "$COMMANDS_DIR/$c"
  done
  echo "    commands -> $COMMANDS_DIR (${#COMMANDS[@]} commands)"

  echo "$PACK_VERSION" > "$RECEIPT"
  echo "    version  -> $PACK_VERSION (receipt: $RECEIPT)"
  echo "Done. Start a new session; run 'python3 -m osa index .' in a project."
}

do_uninstall() {
  echo "==> Uninstalling One Skill Army from $BASE"
  for s in "${SKILLS[@]}"; do rm -rf "$SKILLS_DIR/$s"; done
  for c in "${COMMANDS[@]}"; do rm -f "$COMMANDS_DIR/$c"; done
  prune_retired
  rm -f "$RECEIPT"
  echo "Done. Project memory (.osa/memory/) was left untouched by design."
}

do_doctor() {
  local fail=0 inst="none"
  [ -f "$RECEIPT" ] && inst="$(cat "$RECEIPT" 2>/dev/null)"
  echo "installed version: $inst / source version: $PACK_VERSION  ($BASE)"
  [ "$inst" = "$PACK_VERSION" ] || { echo "NOTE: version drift; re-run '$0 $host' to upgrade."; fail=1; }
  for s in "${RETIRED_SKILLS[@]}"; do
    [ -e "$SKILLS_DIR/$s" ] && { echo "STALE retired skill: $s (re-run installer)"; fail=1; }
  done
  for s in "${SKILLS[@]}"; do
    [ -f "$SKILLS_DIR/$s/SKILL.md" ] || { echo "MISSING skill: $s"; fail=1; }
  done
  for c in "${COMMANDS[@]}"; do
    [ -f "$COMMANDS_DIR/$c" ] || { echo "MISSING command: $c"; fail=1; }
  done
  [ "$fail" = 0 ] && echo "All installed and current."
  exit $fail
}

case "$action" in
  install|--upgrade) do_install ;;
  --uninstall)       do_uninstall ;;
  --doctor)          do_doctor ;;
  *) echo "usage: $0 <claude|gemini|agents|--dir PATH> [--doctor|--uninstall]"; exit 2 ;;
esac
