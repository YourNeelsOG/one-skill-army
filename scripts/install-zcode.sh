#!/usr/bin/env bash
# One Skill Army installer for ZCode (user scope).
#
#   scripts/install-zcode.sh              install skills, commands, hook
#   scripts/install-zcode.sh --upgrade    re-sync to this version (prunes orphans)
#   scripts/install-zcode.sh --agents-compat   also install to ~/.agents/
#   scripts/install-zcode.sh --uninstall  remove everything this script added
#   scripts/install-zcode.sh --doctor     verify install + show version drift
#
# Upgrading: re-running the installer IS the upgrade. It prunes skills and
# commands retired in past versions, copies the current set, and restamps the
# version receipt, so a user on an old version gets fully synced.
#
# What it does:
#   1. Copies skills/  -> ~/.zcode/skills/   (user scope, every workspace)
#   2. Copies commands/ -> ~/.zcode/commands/ (/army, /army-review, ...)
#   3. Installs the SessionStart hook script to ~/.zcode/hooks/ so it keeps
#      working even if this repo is moved or deleted, then MERGES the hook
#      into ~/.zcode/cli/config.json (never overwrites existing config;
#      backs the file up first).
#
# ZCode quirk this script exists for: config-file hooks are disabled unless
# "hooks": { "enabled": true } is set, and the hook command must point at a
# stable path (a repo path with spaces is a quoting trap).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Explicit destination overrides support isolated installs without changing HOME.
ZCODE_BASE="${OSA_ZCODE_BASE:-$HOME/.zcode}"
AGENTS_BASE="${OSA_AGENTS_BASE:-$HOME/.agents}"
ZCODE_SKILLS="$ZCODE_BASE/skills"
ZCODE_COMMANDS="$ZCODE_BASE/commands"
ZCODE_HOOKS="$ZCODE_BASE/hooks"
ZCODE_CONFIG="$ZCODE_BASE/cli/config.json"
HOOK_NAME="one-skill-army-session-start"
REMINDER_NAME="one-skill-army-prompt-reminder"
PACK_NAME="one-skill-army"

# SKILLS, COMMANDS, RETIRED_SKILLS, RETIRED_COMMANDS: single source of truth,
# shared with the generic installer (scripts/install.sh).
# shellcheck source=scripts/pack-manifest.sh
source "$REPO_ROOT/scripts/pack-manifest.sh"

PACK_VERSION="$( (cd "$REPO_ROOT" && python3 -m osa version) 2>/dev/null || echo unknown )"
VERSION_RECEIPT="$ZCODE_BASE/.one-skill-army-version"
COMPAT_RECEIPT="$AGENTS_BASE/.one-skill-army-zcode-version"

# Never replace files inside the source checkout or its ancestors.
python3 - "$REPO_ROOT" "$ZCODE_BASE" "$AGENTS_BASE" <<'PY'
import sys
from pathlib import Path
source = Path(sys.argv[1]).resolve()
for value in sys.argv[2:]:
    target = Path(value).resolve()
    if source == target or source in target.parents or target in source.parents:
        sys.exit("ERROR: install destination must not overlap the source checkout")
PY

backup_config() {
  if [ -f "$ZCODE_CONFIG" ]; then
    cp "$ZCODE_CONFIG" "$ZCODE_CONFIG.bak.$(date +%Y%m%d-%H%M%S)"
  fi
}

merge_hook_config() {
  python3 - "$ZCODE_CONFIG" "$ZCODE_HOOKS/$HOOK_NAME" "$ZCODE_HOOKS/$REMINDER_NAME" "$PACK_NAME" <<'PYEOF'
import json, os, sys

config_path, hook_path, reminder_path, pack_name = sys.argv[1:5]

config = {}
if os.path.exists(config_path):
    with open(config_path) as f:
        config = json.load(f)  # fail loudly on a corrupt config; we backed up first

def is_ours(cmd):
    c = cmd.lower()
    return "one-skill-army" in c or "skill army" in c

hooks = config.setdefault("hooks", {})
hooks["enabled"] = True
events = hooks.setdefault("events", {})

# SessionStart: inject the orchestrator (skipped when defaultMode is off).
session = events.setdefault("SessionStart", [])
hook_entry = {
    "type": "command",
    "command": f'bash "{hook_path}"',
    "shell": "bash",
    "timeout": 10,
    "statusMessage": "Injecting One Skill Army orchestrator",
}
matcher_group = next((g for g in session
                      if g.get("matcher") == "startup|resume|clear|compact"), None)
if matcher_group is None:
    matcher_group = {"matcher": "startup|resume|clear|compact", "hooks": []}
    session.append(matcher_group)
matcher_group["hooks"] = [h for h in matcher_group["hooks"] if not is_ours(h.get("command", ""))]
matcher_group["hooks"].append(hook_entry)

# UserPromptSubmit: one-line reminder on every prompt (drift guard).
prompts = events.setdefault("UserPromptSubmit", [])
reminder_entry = {
    "type": "command",
    "command": f'bash "{reminder_path}"',
    "shell": "bash",
    "timeout": 5,
    "statusMessage": "One Skill Army reminder",
}
prompt_group = next((g for g in prompts if "matcher" not in g), None)
if prompt_group is None:
    prompt_group = {"hooks": []}
    prompts.append(prompt_group)
prompt_group["hooks"] = [h for h in prompt_group["hooks"] if not is_ours(h.get("command", ""))]
prompt_group["hooks"].append(reminder_entry)

os.makedirs(os.path.dirname(config_path), exist_ok=True)
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
print("merged SessionStart + UserPromptSubmit hooks into", config_path)
PYEOF
}

remove_hook_config() {
  python3 - "$ZCODE_CONFIG" "$PACK_NAME" <<'PYEOF'
import json, os, sys

config_path, pack_name = sys.argv[1], sys.argv[2]
if not os.path.exists(config_path):
    sys.exit(0)
with open(config_path) as f:
    config = json.load(f)

hooks = config.get("hooks", {})
events = hooks.get("events", {})
session = events.get("SessionStart", [])
for group in session:
    group["hooks"] = [h for h in group.get("hooks", [])
                      if not ("one-skill-army" in h.get("command", "").lower()
                              or "skill army" in h.get("command", "").lower())]
events["SessionStart"] = [g for g in session if g.get("hooks")]
if not events["SessionStart"]:
    events.pop("SessionStart", None)
prompts = events.get("UserPromptSubmit", [])
for g in prompts:
    g["hooks"] = [h for h in g.get("hooks", [])
                  if not ("one-skill-army" in h.get("command", "").lower()
                          or "skill army" in h.get("command", "").lower())]
events["UserPromptSubmit"] = [g for g in prompts if g.get("hooks")]
if not events["UserPromptSubmit"]:
    events.pop("UserPromptSubmit", None)
if not events:
    hooks.pop("events", None)
# If this pack's uninstall leaves a runner with no events, remove the
# runner config entirely so we don't leave "enabled: true" pointing at nothing.
if not hooks.get("events"):
    config.pop("hooks", None)

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
print("removed hook from", config_path)
PYEOF
}

do_install() {
  echo "==> Installing One Skill Army (ZCode user scope)"
  mkdir -p "$ZCODE_SKILLS" "$ZCODE_COMMANDS" "$ZCODE_HOOKS"

  local prev="none"
  [ -f "$VERSION_RECEIPT" ] && prev="$(cat "$VERSION_RECEIPT" 2>/dev/null)"
  if [ "$prev" != "none" ] && [ "$prev" != "$PACK_VERSION" ]; then
    echo "==> Upgrading from $prev to $PACK_VERSION"
  fi

  # Prune skills/commands retired in past versions so upgrades leave no orphans.
  for s in "${RETIRED_SKILLS[@]}"; do
    rm -rf "$ZCODE_SKILLS/$s" 2>/dev/null
    if [ "${1:-}" = "--agents-compat" ]; then rm -rf "$AGENTS_BASE/skills/$s"; fi
  done
  for c in "${RETIRED_COMMANDS[@]}"; do
    rm -f "$ZCODE_COMMANDS/$c" 2>/dev/null
    if [ "${1:-}" = "--agents-compat" ]; then rm -f "$AGENTS_BASE/commands/$c"; fi
  done

  for s in "${SKILLS[@]}"; do
    if [ ! -d "$REPO_ROOT/skills/$s" ]; then
      echo "ERROR: $REPO_ROOT/skills/$s missing; run from the repo." >&2
      exit 1
    fi
    rm -rf "$ZCODE_SKILLS/$s"
    cp -r "$REPO_ROOT/skills/$s" "$ZCODE_SKILLS/$s"
  done
  echo "    skills    -> $ZCODE_SKILLS (${#SKILLS[@]} skills)"

  for c in "${COMMANDS[@]}"; do
    if [ ! -f "$REPO_ROOT/commands/$c" ]; then
      echo "ERROR: $REPO_ROOT/commands/$c missing." >&2
      exit 1
    fi
    cp "$REPO_ROOT/commands/$c" "$ZCODE_COMMANDS/$c"
  done
  echo "    commands  -> $ZCODE_COMMANDS (${#COMMANDS[@]} commands)"

  # Copy the hook scripts to a stable path so moving/deleting the repo
  # cannot break session start.
  cp "$REPO_ROOT/hooks/session-start" "$ZCODE_HOOKS/$HOOK_NAME"
  cp "$REPO_ROOT/hooks/prompt-reminder" "$ZCODE_HOOKS/$REMINDER_NAME"
  chmod +x "$ZCODE_HOOKS/$HOOK_NAME" "$ZCODE_HOOKS/$REMINDER_NAME"
  echo "    hooks     -> $ZCODE_HOOKS/$HOOK_NAME + $REMINDER_NAME"

  backup_config
  merge_hook_config

  echo "$PACK_VERSION" > "$VERSION_RECEIPT"
  echo "    version   -> $PACK_VERSION (receipt: $VERSION_RECEIPT)"

  echo "==> Smoke test"
  if python3 -c "import json,sys; json.load(open('$ZCODE_CONFIG'))" \
     && env -u CLAUDE_PLUGIN_ROOT -u CURSOR_PLUGIN_ROOT \
        bash "$ZCODE_HOOKS/$HOOK_NAME" \
     | python3 -c "import json,sys; d=json.load(sys.stdin); assert list(d)==['additionalContext'], d.keys()"; then
    echo "    config JSON valid, hook emits strict additionalContext JSON"
  else
    echo "    WARNING: smoke test failed; restore from $ZCODE_CONFIG.bak.* and report." >&2
    exit 1
  fi

  cat <<EOF

Done. Start a NEW session (or /clear) to load the pack.

Try:
  /army ultra
  "add a date picker to a form"          # should reach for <input type="date">
  "remember that we deploy via make deploy"
EOF

  if [ "${1:-}" = "--agents-compat" ]; then
    mkdir -p "$AGENTS_BASE/skills" "$AGENTS_BASE/commands"
    for s in "${SKILLS[@]}"; do
      rm -rf "$AGENTS_BASE/skills/$s"
      cp -r "$REPO_ROOT/skills/$s" "$AGENTS_BASE/skills/$s"
    done
    for c in "${COMMANDS[@]}"; do
      cp "$REPO_ROOT/commands/$c" "$AGENTS_BASE/commands/$c"
    done
    echo "$PACK_VERSION" > "$COMPAT_RECEIPT"
    echo "==> also installed to $AGENTS_BASE/{skills,commands} (cross-tool scope)"
  fi
}

do_uninstall() {
  echo "==> Uninstalling One Skill Army (ZCode user scope)"
  for s in "${SKILLS[@]}"; do rm -rf "$ZCODE_SKILLS/$s"; done
  for c in "${COMMANDS[@]}"; do rm -f "$ZCODE_COMMANDS/$c"; done
  for s in "${RETIRED_SKILLS[@]}"; do rm -rf "$ZCODE_SKILLS/$s" 2>/dev/null; done
  for c in "${RETIRED_COMMANDS[@]}"; do rm -f "$ZCODE_COMMANDS/$c" 2>/dev/null; done
  rm -f "$ZCODE_HOOKS/$HOOK_NAME" "$ZCODE_HOOKS/$REMINDER_NAME"
  if [ -f "$COMPAT_RECEIPT" ]; then
    for s in "${SKILLS[@]}"; do rm -rf "$AGENTS_BASE/skills/$s"; done
    for c in "${COMMANDS[@]}"; do rm -f "$AGENTS_BASE/commands/$c"; done
    rm -f "$COMPAT_RECEIPT"
  fi
  rm -f "$VERSION_RECEIPT" 2>/dev/null
  backup_config
  remove_hook_config
  echo "Done. Project memory (.osa/memory/) was left untouched by design."
}

do_doctor() {
  local fail=0
  local inst="none"
  [ -f "$VERSION_RECEIPT" ] && inst="$(cat "$VERSION_RECEIPT" 2>/dev/null)"
  echo "installed version: $inst / pack version: $PACK_VERSION"
  if [ "$inst" != "$PACK_VERSION" ]; then
    echo "NOTE: version drift; re-run 'scripts/install-zcode.sh' to upgrade."
    fail=1
  fi
  for s in "${RETIRED_SKILLS[@]}"; do
    [ -e "$ZCODE_SKILLS/$s" ] && { echo "STALE retired skill present: $s (re-run installer)"; fail=1; }
  done
  for c in "${RETIRED_COMMANDS[@]}"; do
    [ -e "$ZCODE_COMMANDS/$c" ] && { echo "STALE retired command present: $c (re-run installer)"; fail=1; }
  done
  for s in "${SKILLS[@]}"; do
    [ -f "$ZCODE_SKILLS/$s/SKILL.md" ] || { echo "MISSING skill: $s"; fail=1; }
  done
  for c in "${COMMANDS[@]}"; do
    [ -f "$ZCODE_COMMANDS/$c" ] || { echo "MISSING command: $c"; fail=1; }
  done
  [ -x "$ZCODE_HOOKS/$HOOK_NAME" ] || { echo "MISSING hook: $ZCODE_HOOKS/$HOOK_NAME"; fail=1; }
  [ -x "$ZCODE_HOOKS/$REMINDER_NAME" ] || { echo "MISSING hook: $ZCODE_HOOKS/$REMINDER_NAME"; fail=1; }
  grep -q "$REMINDER_NAME" "$ZCODE_CONFIG" 2>/dev/null || { echo "reminder hook not registered"; fail=1; }
  if [ -f "$ZCODE_CONFIG" ]; then
    grep -q '"enabled": true' "$ZCODE_CONFIG" || { echo "hooks.enabled not true in $ZCODE_CONFIG"; fail=1; }
    grep -q "$HOOK_NAME" "$ZCODE_CONFIG" || { echo "hook not registered in $ZCODE_CONFIG"; fail=1; }
  else
    echo "MISSING config: $ZCODE_CONFIG"; fail=1
  fi
  [ "$fail" = 0 ] && echo "All installed. New sessions have the pack."
  exit $fail
}

case "${1:-install}" in
  install)          do_install "${2:-}" ;;
  --upgrade)        do_install "${2:-}" ;;   # re-run: prunes orphans, copies new, restamps version
  --agents-compat)  do_install --agents-compat ;;
  --uninstall)      do_uninstall ;;
  --doctor)         do_doctor ;;
  *) echo "usage: $0 [install|--upgrade|--agents-compat|--uninstall|--doctor]"; exit 2 ;;
esac
