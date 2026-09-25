#!/usr/bin/env python3
"""Structural tests for the One Skill Army skill pack.

Verifies every skill is loadable (frontmatter + required sections),
commands exist, cross-references resolve, and the pack's invariants
(iron laws, never-compress list, blocklisted reviewers, em-dash ban)
are present. No external deps.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print(f"  ok: {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL: {name} {detail}")


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        m2 = re.match(r"^(\w[-\w]*):\s*(.*)$", line)
        if m2:
            fm[m2.group(1)] = m2.group(2).strip()
    return fm


REQUIRED_SKILLS = [
    "one-skill-army", "memory", "minimal-code", "token-discipline", "workflow",
    "test-driven-development", "systematic-debugging",
    "verification-before-completion", "anti-hallucination",
    "code-commenting", "git-safety", "army-commit", "input-discipline",
    "mapit", "writing-plans", "subagent-driven-development", "code-review",
    "using-git-worktrees",
]

REQUIRED_MANIFESTS = [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
                      ".cursor-plugin/plugin.json", ".codex-plugin/plugin.json",
                      "hooks/hooks.json", "hooks/hooks-cursor.json"]

REQUIRED_COMMANDS = ["army", "army-review", "army-audit", "army-debt",
                     "army-help", "army-gain", "army-compress"]

REQUIRED_ADAPTERS = ["claude", "codex", "grok", "cursor", "gemini", "zcode",
                     "opencode"]

REQUIRED_MANIFESTS = [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
                      ".cursor-plugin/plugin.json", ".codex-plugin/plugin.json",
                      ".zcode-plugin/plugin.json",
                      "hooks/hooks.json", "hooks/hooks-cursor.json"]

print("skills:")
skills = {}
for skill in REQUIRED_SKILLS:
    path = ROOT / "skills" / skill / "SKILL.md"
    check(f"{skill}/SKILL.md exists", path.is_file())
    if not path.is_file():
        continue
    text = path.read_text()
    skills[skill] = text
    fm = parse_frontmatter(text)
    check(f"{skill} has frontmatter", fm is not None)
    check(f"{skill} has name", bool(fm and fm.get("name")))
    check(f"{skill} has description", bool(fm and fm.get("description")))
    check(f"{skill} has boundaries or scope section",
          any(s in text for s in ("Boundaries", "When to Use", "When NOT",
                                  "When to Apply", "Persistence",
                                  "Quick Reference")))

print("commands:")
ARG_TAKING = set(REQUIRED_COMMANDS) - {"army-help", "army-gain"}  # info cards take no args
for cmd in REQUIRED_COMMANDS:
    path = ROOT / "commands" / f"{cmd}.md"
    check(f"commands/{cmd}.md exists", path.is_file())
    if path.is_file():
        text = path.read_text()
        check(f"{cmd} has description", "description:" in text)
        if cmd in ARG_TAKING:
            check(f"{cmd} substitutes $ARGUMENTS", "$ARGUMENTS" in text)
        else:
            check(f"{cmd} takes no args", "$ARGUMENTS" not in text)

print("adapters:")
for adapter in REQUIRED_ADAPTERS:
    check(f"adapters/{adapter}.md exists",
          (ROOT / "adapters" / f"{adapter}.md").is_file())
grok_txt = (ROOT / "adapters/grok.md").read_text()
check("grok adapter: plugins disabled by default", "DISABLED by default" in grok_txt
      or "off by default" in grok_txt.lower())
check("grok adapter: hooks-cannot-inject caveat", "cannot inject" in grok_txt)
check("grok adapter: config.toml enable", "config.toml" in grok_txt)
oc = ROOT / ".opencode/plugins/one-skill-army.mjs"
check("opencode plugin exists", oc.is_file())
if oc.is_file():
    oc_txt = oc.read_text()
    check("opencode plugin registers skills+commands", "skills.paths" in oc_txt
          and "config.command" in oc_txt)
    check("opencode plugin per-turn reminder", "experimental.chat.system.transform" in oc_txt)
    check("opencode plugin respects off mode", '"off"' in oc_txt)
check("grok marketplace manifest exists",
      (ROOT / ".grok-plugin/marketplace.json").is_file())

print("cross-references:")
orch = skills.get("one-skill-army", "")
for skill in REQUIRED_SKILLS[1:]:
    check(f"orchestrator references {skill}", skill in orch)
check("orchestrator states priority order", "git-safety > anti-hallucination" in orch)

print("iron laws and invariants:")
check("tdd iron law", "FAILING TEST FIRST" in skills["test-driven-development"])
check("debugging iron law", "ROOT CAUSE INVESTIGATION FIRST" in skills["systematic-debugging"])
check("verification iron law", "NO COMPLETION CLAIMS WITHOUT FRESH" in skills["verification-before-completion"])
check("anti-hallucination iron law", "NOT READ THIS SESSION" in skills["anti-hallucination"])
check("git-safety iron law", "WITHOUT EXPLICIT USER APPROVAL" in skills["git-safety"])
check("commenting iron law", "NO EM DASHES" in skills["code-commenting"])

td = skills["token-discipline"]
check("token-discipline iron law", "Iron Law" in td)
check("token-discipline protects code/paths/errors",
      "NEVER" in td.upper() and "error" in td.lower())
check("token-discipline has auto-clarity", "Auto-Clarity" in td)
check("token-discipline has intensity examples", "re-render" in td)
check("token-discipline bans em dashes in replies",
      "No em dashes" in td and "chat included" in td)
check("token-discipline rejects non-levels",
      '"high"' in td and "Never map" in td)

print("em-dash hygiene:")
allowed = re.compile(r"BAD|❌|Also BAD|em dashes \(—\)")
for md in ROOT.rglob("*.md"):
    rel = md.relative_to(ROOT)
    # Skip generated output; the em-dash ban is for authored source only.
    if {".git", "node_modules", "graphify-out", ".osa"} & set(rel.parts):
        continue
    for i, line in enumerate(md.read_text().splitlines(), 1):
        if "—" in line and not allowed.search(line):
            check(f"em-dash-free {rel}:{i}", False, line.strip()[:60])
            break
    else:
        continue
check("army command never guesses levels", "Never guess" in (ROOT / "commands/army.md").read_text())

mc = skills["minimal-code"]
check("minimal-code has ladder", "The Ladder" in mc)
check("minimal-code has 7 rungs", "7. " in mc or "**Only then:**" in mc)
check("minimal-code has Two Questions", "The Two Questions" in mc
      and "shorter and still do the same work" in mc)
check("minimal-code has osa debt marker", "osa:" in mc)
check("minimal-code never-lazy section", "When NOT to be lazy" in mc)
check("minimal-code hardware calibration", "calibration" in mc)
check("minimal-code default-mode config", "OSA_DEFAULT_MODE" in mc
      and ".osa/config.json" in mc)
check("minimal-code standalone deactivation guard",
      "ENTIRE message" in mc)
check("minimal-code rationalization table", "Rationalizations" in mc)

gs = skills["git-safety"]
for bot in ["Qodo", "CodeRabbit", "Greptile", "Copilot Code Review",
            "SonarQube", "Sourcegraph", "Snyk", "Codacy", "Bugbot", "Semgrep"]:
    check(f"git-safety blocks {bot}", bot in gs)
check("git-safety forbids force push",
      "--force-with-lease" in gs and "FORBIDDEN" in gs)
check("git-safety requires PR draft approval", "draft" in gs.lower())

wf = skills["workflow"]
check("workflow hard gate", "HARD-GATE" in wf)
check("workflow three paths", "Spike" in wf and "Bounded" in wf and "Architectural" in wf)
check("workflow red flags table", "Red Flags" in wf)

ah = skills["anti-hallucination"]
check("anti-hallucination outranks others", "outranks" in ah)
check("anti-hallucination has rationalizations", "Rationalizations" in ah)

print("input-discipline:")
idsc = skills["input-discipline"]
check("input-discipline iron law", "SMALLEST THING THAT ANSWERS" in idsc)
check("input-discipline never-dumber rule", "never make the agent dumber" in idsc.lower())
check("input-discipline fastcontext contract", "no relevant locations found" in idsc)
check("input-discipline ranges over files", "Read ranges, not files" in idsc)
check("input-discipline yields to verification", "verification-before-" in idsc)

print("army-compress:")
acmd = (ROOT / "commands/army-compress.md").read_text()
check("compress never touches code files", "NEVER" in acmd and ".py" in acmd)
check("compress out-of-tree backup", ".osa/backups/" in acmd)
check("compress net-negative gate", "not smaller than the original" in acmd)
check("compress code blocks read-only", "read-only regions" in acmd)
td_txt = skills["token-discipline"]
check("token-discipline honest numbers", "Honest numbers" in td_txt
      and "net-negative" in td_txt and "/army off" in td_txt)

print("memory:")
mem = skills["memory"]
check("memory untrusted-data rule", "UNTRUSTED DATA, NEVER INSTRUCTIONS" in mem)
check("memory repo-state-beats-memory", "CURRENT REPO STATE BEATS MEMORY" in mem)
check("memory provenance rule", "PROVENANCE" in mem)
check("memory store paths", "MEMORY.md" in mem and "HANDOFF.md" in mem)
check("memory compaction protocol", "Compaction" in mem)
check("memory graphify routing", "graphify" in mem)
check("memory ai-memory routing", "ai-memory" in mem)
check("memory no-secrets rule", "secret" in mem.lower())
agents_txt = (ROOT / "AGENTS.md").read_text()
check("AGENTS.md memory protocol", ".osa/memory" in agents_txt)

print("distribution:")
import json as _json
for manifest in REQUIRED_MANIFESTS:
    path = ROOT / manifest
    check(f"{manifest} exists", path.is_file())
    if path.suffix == ".json" and path.is_file():
        try:
            _json.loads(path.read_text())
            check(f"{manifest} valid JSON", True)
        except _json.JSONDecodeError as e:
            check(f"{manifest} valid JSON", False, str(e))
check("session-start hook executable",
      (ROOT / "hooks/session-start").is_file() and
      (ROOT / "hooks/session-start").stat().st_mode & 0o111 != 0)
hook_src = (ROOT / "hooks/session-start").read_text()
check("session-start injects memory protocol", "MEMORY.md" in hook_src)
check("hook always exits 0", "exit 0" in hook_src)
check("hook no set -e (must always emit JSON)", "-euo" not in hook_src)
check("hook has missing-file fallback", "orchestrator file is missing" in hook_src)
check("hook emits plain additionalContext fallback", '"additionalContext"' in hook_src)

print("installer:")
inst = ROOT / "scripts/install-zcode.sh"
check("install-zcode.sh exists", inst.is_file())
if inst.is_file():
    check("install-zcode.sh executable", inst.stat().st_mode & 0o111 != 0)
    src = inst.read_text()
    check("installer backs up config", "backup" in src.lower())
    check("installer merges JSON not overwrite", "json.load" in src)
    check("installer idempotent dedup", "is_ours" in src)
    check("installer uses stable hook path", "one-skill-army-session-start" in src)
    check("installer registers prompt reminder", "UserPromptSubmit" in src
          and "prompt-reminder" in src)
    check("installer supports uninstall", "--uninstall" in src)
    check("installer supports doctor", "--doctor" in src)
rem = ROOT / "hooks/prompt-reminder"
check("prompt-reminder hook exists+executable",
      rem.is_file() and rem.stat().st_mode & 0o111 != 0)
if rem.is_file():
    rtxt = rem.read_text()
    check("reminder drift-guard content", "ladder before code" in rtxt
          and "verify before claiming" in rtxt)
    check("reminder always exits 0", "exit 0" in rtxt)
gain = (ROOT / "commands/army-gain.md").read_text()
check("army-gain honesty rule", "NEVER invent a savings number" in gain)
check("orchestrator lists memory", "memory" in orch)

ac = skills["army-commit"]
check("army-commit conventional types", "feat" in ac and "revert" in ac)
check("army-commit never-list", "NEVER" in ac)

check("AGENTS.md exists", (ROOT / "AGENTS.md").is_file())
agents = (ROOT / "AGENTS.md").read_text()
check("AGENTS.md covers iron laws", "FAILING TEST FIRST" in agents
      and "ROOT-CAUSE" in agents and "NO COMPLETION CLAIMS" in agents)
check("AGENTS.md covers commenting rules", "em dash" in agents.lower()
      and "banner" in agents.lower())
check("AGENTS.md covers git safety", "force push" in agents.lower()
      and "CodeRabbit" in agents)
check("AGENTS.md forbids committing env files",
      ".env.local" in agents and "database dump" in agents.lower())
check("AGENTS.md forbids AI mentions in commits/PRs",
      "AI tool" in agents and "PR description" in agents)
check("AGENTS.md names hook enforcement", "hooks/git" in agents)
check("README exists", (ROOT / "README.md").is_file())
check("examples exist", (ROOT / "examples/example-prompts.md").is_file())

print("git hook enforcement:")
import subprocess as _sp
import tempfile as _tf

def _fresh_repo():
    d = _tf.mkdtemp(prefix="osa-hook-")
    _sp.run(["git", "init", "-q"], cwd=d, check=True)
    return d

def _run_hook(hook_name, repo, *args):
    hook = ROOT / "hooks" / "git" / hook_name
    return _sp.run(["bash", str(hook), *args], cwd=repo,
                   capture_output=True, text=True)

pre = ROOT / "hooks/git/pre-commit"
check("pre-commit hook exists+executable",
      pre.is_file() and pre.stat().st_mode & 0o111 != 0)
if pre.is_file():
    for name in [".env", ".env.local", ".env.production",
                 "dump.sql", "backup.dump", "data.sqlite", "app.db"]:
        d = _fresh_repo()
        (Path(d) / name).write_text("secret\n")
        _sp.run(["git", "add", name], cwd=d, check=True)
        r = _run_hook("pre-commit", d)
        check(f"pre-commit blocks {name}",
              r.returncode != 0 and name in (r.stdout + r.stderr),
              (r.stdout + r.stderr).strip()[:80])
    for name in ["README.md", "notes.txt", ".env.example"]:
        d = _fresh_repo()
        (Path(d) / name).write_text("safe\n")
        _sp.run(["git", "add", name], cwd=d, check=True)
        r = _run_hook("pre-commit", d)
        check(f"pre-commit allows {name}", r.returncode == 0,
              (r.stdout + r.stderr).strip()[:80])

cm = ROOT / "hooks/git/commit-msg"
check("commit-msg hook exists+executable",
      cm.is_file() and cm.stat().st_mode & 0o111 != 0)
if cm.is_file():
    for bad in ["feat: add thing\n\nGenerated with Cursor\n",
                "feat: add thing\n\nCo-Authored-By: Cursor <noreply@cursor.sh>\n",
                "feat: add thing\n\nthanks Claude for the help\n",
                "fix: use GPT to parse\n"]:
        d = _fresh_repo()
        msg = Path(d) / "COMMIT_EDITMSG"
        msg.write_text(bad)
        r = _run_hook("commit-msg", d, str(msg))
        check(f"commit-msg blocks: {bad.splitlines()[-1][:35]}",
              r.returncode != 0, (r.stdout + r.stderr).strip()[:80])
    d = _fresh_repo()
    msg = Path(d) / "COMMIT_EDITMSG"
    msg.write_text("feat: add thing\n\nfix pointer jitter in the UI\n")
    r = _run_hook("commit-msg", d, str(msg))
    check("commit-msg allows clean message", r.returncode == 0,
          (r.stdout + r.stderr).strip()[:80])

instg = ROOT / "scripts/install-git-hooks.sh"
check("install-git-hooks.sh exists+executable",
      instg.is_file() and instg.stat().st_mode & 0o111 != 0)
if instg.is_file():
    d = _fresh_repo()
    _sp.run(["bash", str(instg)], cwd=d, check=True, capture_output=True)
    for h in ["pre-commit", "commit-msg"]:
        p = Path(d) / ".githooks" / h
        check(f"installer copies {h}", p.is_file() and p.stat().st_mode & 0o111 != 0)
    hooks_path = _sp.run(["git", "config", "core.hooksPath"], cwd=d,
                         capture_output=True, text=True).stdout.strip()
    check("installer sets core.hooksPath", hooks_path == ".githooks", hooks_path)
    check("installer idempotent",
          _sp.run(["bash", str(instg)], cwd=d, capture_output=True).returncode == 0)
    (Path(d) / ".env").write_text("secret\n")
    _sp.run(["git", "add", ".env"], cwd=d, check=True)
    _sp.run(["git", "config", "user.email", "t@t"], cwd=d, check=True)
    _sp.run(["git", "config", "user.name", "t"], cwd=d, check=True)
    r = _sp.run(["git", "commit", "-m", "feat: x"], cwd=d,
                capture_output=True, text=True)
    check("installed hooks block protected commit",
          r.returncode != 0 and ".env" in (r.stdout + r.stderr))
    (Path(d) / ".env").unlink()
    _sp.run(["git", "rm", "--cached", ".env"], cwd=d, check=True)
    (Path(d) / "a.txt").write_text("ok\n")
    _sp.run(["git", "add", "a.txt"], cwd=d, check=True)
    r = _sp.run(["git", "commit", "-m", "feat: add a"], cwd=d,
                capture_output=True, text=True)
    check("installed hooks allow clean commit", r.returncode == 0,
          (r.stdout + r.stderr).strip()[:80])

print("graphify script:")
gs = ROOT / "skills/mapit/osa-graph-stale.py"
check("osa-graph-stale.py exists", gs.is_file())
if gs.is_file():
    def _run_py(args, cwd):
        return _sp.run(["python3", str(gs), *args], cwd=cwd,
                       capture_output=True, text=True)
    gdir = _tf.mkdtemp(prefix="osa-graph-")
    (Path(gdir) / "src").mkdir()
    (Path(gdir) / "src" / "a.py").write_text("print(1)\n")
    r = _run_py([], gdir)
    check("graphify: no-manifest message", r.returncode == 0
          and "manifest" in (r.stdout + r.stderr).lower())
    r = _run_py(["--update"], gdir)
    mf = Path(gdir) / ".osa/graph/manifest.jsonl"
    check("graphify: --update writes manifest", r.returncode == 0 and mf.is_file())
    if mf.is_file():
        check("graphify: manifest lists src/a.py", "src/a.py" in mf.read_text())
    r = _run_py([], gdir)
    out = r.stdout
    check("graphify: clean tree no changes", r.returncode == 0
          and "MODIFIED " not in out and "ADDED " not in out
          and "DELETED " not in out)
    (Path(gdir) / "src" / "a.py").write_text("print(2)\n")
    (Path(gdir) / "src" / "b.py").write_text("x\n")
    r = _run_py([], gdir)
    check("graphify: detects modify", "MODIFIED src/a.py" in r.stdout, r.stdout[:120])
    check("graphify: detects add", "ADDED src/b.py" in r.stdout, r.stdout[:120])
    check("graphify: skips .osa files", "manifest.jsonl" not in r.stdout)
    _run_py(["--update"], gdir)
    (Path(gdir) / "src" / "b.py").unlink()
    r = _run_py([], gdir)
    check("graphify: detects delete", "DELETED src/b.py" in r.stdout, r.stdout[:120])
    (Path(gdir) / "node_modules").mkdir()
    (Path(gdir) / "node_modules" / "x.js").write_text("j\n")
    r = _run_py(["--update"], gdir)
    check("graphify: skips node_modules", "node_modules" not in mf.read_text())
    (Path(gdir) / ".osa" / "graph" / "nodes.jsonl").write_text(
        '{"id": "src/a.py", "kind": "file", "summary": "entry"}\n')
    (Path(gdir) / ".osa" / "graph" / "edges.jsonl").write_text(
        '{"from": "src/a.py", "rel": "imports", "to": "src/b.py", '
        '"seen": "2026-09-12", "evidence": "import a"}\n')
    r = _run_py(["--html"], gdir)
    gh = Path(gdir) / ".osa/graph/graph.html"
    check("graphify: --html writes graph.html", r.returncode == 0 and gh.is_file())
    if gh.is_file():
        html = gh.read_text()
        check("graphify: html has node id", "src/a.py" in html)
        check("graphify: html has edge target", "src/b.py" in html)
        check("graphify: html self-contained", "https://" not in html
              and "http://" not in html)

print("graphify pack wiring:")
gskill = ROOT / "skills/mapit/SKILL.md"
check("graphify skill exists", gskill.is_file())
if gskill.is_file():
    gt = gskill.read_text()
    check("graphify source-of-truth rule", "source of truth" in gt.lower())
    check("graphify staleness script contract",
          "osa-graph-stale.py" in gt and "--update" in gt)
    check("graphify html viz", "graph.html" in gt and "--html" in gt)
    check("graphify edge recording discipline",
          "edges.jsonl" in gt and "evidence" in gt)
gcmd = ROOT / "commands/mapit.md"
check("mapit command exists", gcmd.is_file())
if gcmd.is_file():
    check("graphify command description", "description:" in gcmd.read_text())
check("memory routes to native graph",
      "osa context" in skills.get("memory", "")
      and ".osa/context.md" in skills.get("memory", ""))
check("AGENTS.md native graph route",
      "osa context" in agents and ".osa/context.md" in agents)
check("orchestrator routes mapit", "mapit" in orch)

print("mapit rename:")
manifest_sh = (ROOT / "scripts/pack-manifest.sh").read_text()
check("osa-map skill retired", "RETIRED_SKILLS=(graphify osa-map)" in manifest_sh)
check("osa-map command retired",
      "RETIRED_COMMANDS=(graphify.md osa-map.md)" in manifest_sh)
check("old osa-map dirs gone", not (ROOT / "skills/osa-map").exists()
      and not (ROOT / "commands/osa-map.md").exists())
# Rename history ("osa-map renamed to mapit") is the one allowed mention.
live_refs = [str(f.relative_to(ROOT)) + ":" + line.strip()[:60]
             for f in ROOT.rglob("*")
             if f.is_file() and f.suffix in (".md", ".sh", ".json", ".py")
             and not {".git", ".osa", "docs"} & set(f.relative_to(ROOT).parts)
             and f.name not in ("test_structure.py", "pack-manifest.sh")
             for line in f.read_text(errors="ignore").splitlines()
             if "osa-map" in line and "rename" not in line]
check("no live osa-map references", not live_refs, str(live_refs))

print("version sync:")
import json as _json
import re as _re
src_version = _re.search(r'__version__ = "([^"]+)"',
                         (ROOT / "osa/__init__.py").read_text()).group(1)
for mpath in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json",
              ".cursor-plugin/plugin.json", ".zcode-plugin/plugin.json"):
    data = _json.loads((ROOT / mpath).read_text())
    check("version " + mpath, data.get("version") == src_version,
          str(data.get("version")))
mkt = _json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
check("version marketplace",
      all(pl.get("version") == src_version for pl in mkt["plugins"]))

print()
if FAILURES:
    print(f"{len(FAILURES)} failure(s): {FAILURES}")
    sys.exit(1)
print("All structure tests passed.")
