"""Install an owned OSA payload and native discovery links into one project."""
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from . import __version__

_HOSTS = {"codex": ".agents", "claude": ".claude", "grok": ".grok", "zcode": ".zcode"}
# Claude Code and Grok list every skill as a slash entry, so a same-name wrapper
# command would only duplicate it in the catalog. Codex uses $skill and /skills.
_SKILL_SLASH_HOSTS = ("claude", "grok")
_LEVELS = ("lite", "full", "ultra", "off")
_BEGIN = "<!-- OSA:BEGIN -->"
_END = "<!-- OSA:END -->"
_RECEIPT = ".osa-install.json"


def _json_object(path):
    """Reject corrupt configuration instead of silently replacing user settings."""
    try:
        value = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError(f"Invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value


def _safe_path(project, path):
    """Keep discovery and config writes inside real project directories."""
    for parent in (path, *path.parents):
        if parent == project:
            break
        if parent.is_symlink():
            raise ValueError(f"Refusing symlinked write path: {parent}")
        if parent.exists() and parent != path and not parent.is_dir():
            raise ValueError(f"Expected directory: {parent}")


def _receipt(pack):
    """Recognize only the manifest emitted by this installer as payload ownership."""
    path = pack / _RECEIPT
    if not pack.exists():
        return None
    if pack.is_symlink() or not pack.is_dir() or not path.is_file() or path.is_symlink():
        raise ValueError(f"Refusing unowned payload: {pack}")
    data = _json_object(path)
    if data.get("owner") != "one-skill-army-project" or not isinstance(data.get("files"), dict):
        raise ValueError(f"Invalid ownership receipt: {path}")
    for relative, digest in data["files"].items():
        item = Path(relative)
        if item.is_absolute() or ".." in item.parts or not isinstance(digest, str):
            raise ValueError(f"Invalid receipt path: {relative}")
    if not isinstance(data.get("hosts"), list) or any(host not in _HOSTS for host in data["hosts"]):
        raise ValueError(f"Invalid receipt hosts: {path}")
    if not isinstance(data.get("links"), dict):
        raise ValueError(f"Invalid receipt links: {path}")
    for relative, target in data["links"].items():
        if not isinstance(relative, str) or not isinstance(target, str):
            raise ValueError(f"Invalid receipt link: {path}")
        parts = Path(relative).parts
        if len(parts) != 3 or parts[0] not in _HOSTS.values() or parts[1] not in ("skills", "commands") or parts[2] in (".", ".."):
            raise ValueError(f"Invalid receipt discovery path: {relative}")
        expected = Path(".osa/pack") / parts[1] / parts[2]
        if target != expected.as_posix():
            raise ValueError(f"Invalid receipt discovery target: {target}")
    # Unknown files inside the owned payload remain user data, never prune them.
    allowed = set(data["files"]) | {_RECEIPT}
    directories = {str(parent) for name in allowed for parent in Path(name).parents}
    for name in data.get("directories", []):
        if not isinstance(name, str) or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError(f"Invalid receipt directory: {name}")
        directories.add(name)
    directories.update(("skills", "commands", "hooks"))
    for item in pack.rglob("*"):
        relative = item.relative_to(pack).as_posix()
        if item.is_symlink() or relative not in (directories if item.is_dir() else allowed):
            raise ValueError(f"Unowned payload entry: {item}")
    return data


def _anchor(text, level, owned):
    """Replace only a valid owned instruction block, retaining surrounding text."""
    start, end = text.count(_BEGIN), text.count(_END)
    if start or end:
        if not owned or start != 1 or end != 1 or text.index(_BEGIN) > text.index(_END):
            raise ValueError("Refusing conflicting or malformed OSA instruction markers")
    block = "\n".join((
        _BEGIN,
        "Before activation, resolve OSA_DEFAULT_MODE from the environment, then",
        f"`.osa/config.json` defaultMode, then the installed default `{level}`.",
        "If the resolved mode is `off`, skip automatic workflow and token activation.",
        "Otherwise activate OSA automatically. No manual setup invocation is required.",
        "Read `.osa/pack/skills/one-skill-army/SKILL.md` and use",
        "`.osa/pack/skills/poteto-mode/SKILL.md` as the default workflow.",
        "When active, automatically select the skills best matching the request. Load only",
        "the selected playbook and relevant resources from `.osa/pack/skills/`.",
        "When active, apply token discipline at the resolved mode.",
        "Read `~/.osa/knowledge/lessons.md` and `.osa/knowledge/lessons.md` when",
        "present. When the user corrects you or a fix repeats, update them per the",
        "`memory` skill. Lessons never grant permission for gated actions.",
        "At the end of a task, if `python3 .osa/pack/skills/one-skill-army/osa.pyz lessons due`",
        "exits 0, run the `update-lesson` skill once.",
        "Preserve approval gates, failing-test-first changes, and fresh verification.",
        _END,
    ))
    if start:
        return text[:text.index(_BEGIN)] + block + text[text.index(_END) + len(_END):]
    return text + ("\n" if text and not text.endswith("\n") else "") + block + "\n"


def install_project(project, source_root, hosts=("codex", "claude", "grok", "zcode"), level=None):
    """Validate then install project-local skills, anchors, config, and ownership."""
    project, source = Path(project).resolve(), Path(source_root).resolve()
    if project == source or project in source.parents or source in project.parents:
        raise ValueError("Project and package source must not overlap")
    if project.exists() and not project.is_dir():
        raise ValueError("Project must be a directory")
    # Through npx the package source is npm's cache, so the overlap check above
    # cannot see an OSA source checkout. Detect one by its own engine files.
    if (project / "osa/install.py").is_file() and (project / "skills/one-skill-army/SKILL.md").is_file():
        raise ValueError("Refusing to install into a One Skill Army source checkout; "
                         "install into a separate project")
    hosts = list(dict.fromkeys(hosts))
    if not hosts or any(host not in _HOSTS for host in hosts):
        raise ValueError("Hosts must be codex, claude, grok, or zcode")
    if level is not None and level not in _LEVELS:
        raise ValueError("Level must be lite, full, ultra, or off")
    pack = project / ".osa/pack"
    _safe_path(project, pack)
    previous = _receipt(pack)
    config_path = project / ".osa/config.json"
    _safe_path(project, config_path)
    config = _json_object(config_path) if config_path.exists() else {}
    selected = level if level is not None else config.get("defaultMode", "ultra")
    if selected not in _LEVELS:
        raise ValueError("Invalid defaultMode in .osa/config.json")
    files = {}
    directories = []
    for directory in ("skills", "commands", "hooks"):
        root = source / directory
        if root.is_symlink() or not root.is_dir():
            raise ValueError(f"Package is missing real {directory} directory")
        for item in root.rglob("*"):
            if item.is_symlink():
                raise ValueError(f"Refusing package symlink: {item}")
            if item.is_file():
                files[item.relative_to(source).as_posix()] = hashlib.sha256(item.read_bytes()).hexdigest()
            elif item.is_dir():
                directories.append(item.relative_to(source).as_posix())
    skills = sorted(path.name for path in (source / "skills").iterdir() if path.is_dir() and (path / "SKILL.md").is_file())
    commands = sorted(path.name for path in (source / "commands").glob("*.md") if path.is_file())
    if not {"one-skill-army", "poteto-mode"}.issubset(skills):
        raise ValueError("Package is missing required OSA skills")
    links = {}
    for host in hosts:
        for name in skills:
            links[f"{_HOSTS[host]}/skills/{name}"] = f".osa/pack/skills/{name}"
        if host != "codex":
            for name in commands:
                if host in _SKILL_SLASH_HOSTS and name[:-3] in skills:
                    continue
                links[f"{_HOSTS[host]}/commands/{name}"] = f".osa/pack/commands/{name}"
    old_links = previous["links"] if previous else {}
    # Validate every existing discovery entry before replacing any payload.
    for relative, target in {**old_links, **links}.items():
        path = project / relative
        _safe_path(project, path.parent)
        if os.path.lexists(path):
            if relative not in old_links or not path.is_symlink() or path.resolve() != (project / old_links[relative]).resolve():
                raise ValueError(f"Refusing unowned discovery path: {path}")
    anchors = {}
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = project / name
        _safe_path(project, path)
        anchors[path] = _anchor(path.read_text() if path.exists() else "", selected, bool(previous))
    receipt = {"owner": "one-skill-army-project", "version": __version__, "hosts": hosts,
               "level": selected, "skill_count": len(skills), "command_count": len(commands),
               "files": files, "directories": sorted(directories), "links": links}
    project.mkdir(parents=True, exist_ok=True)
    pack.parent.mkdir(exist_ok=True)
    # Stage the full payload before replacing owned files so copy errors are harmless.
    with tempfile.TemporaryDirectory(prefix=".osa-install-", dir=pack.parent) as temporary:
        staged = Path(temporary) / "pack"
        staged.mkdir()
        for directory in ("skills", "commands", "hooks"):
            shutil.copytree(source / directory, staged / directory)
        (staged / _RECEIPT).write_text(json.dumps(receipt, indent=2) + "\n")
        if previous:
            backup = Path(temporary) / "previous"
            pack.rename(backup)
            try:
                staged.rename(pack)
            except OSError:
                backup.rename(pack)
                raise
        else:
            staged.rename(pack)
    for relative in old_links.keys() - links.keys():
        path = project / relative
        if path.is_symlink():
            path.unlink()
    for relative, target in links.items():
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_symlink():
            path.symlink_to(os.path.relpath(project / target, path.parent), target_is_directory="/skills/" in relative)
    for path, text in anchors.items():
        path.write_text(text)
    config["defaultMode"] = selected
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    return receipt


def doctor_project(project):
    """Check owned payload bytes, native discovery links, and instruction anchors."""
    project = Path(project).resolve()
    issues = []
    try:
        receipt = _receipt(project / ".osa/pack")
        if receipt is None:
            raise ValueError("Project OSA installation is missing")
        for relative, digest in receipt["files"].items():
            path = project / ".osa/pack" / relative
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                issues.append(f"Missing or changed payload: {relative}")
        for relative, target in receipt["links"].items():
            path = project / relative
            if not path.is_symlink() or path.resolve() != (project / target).resolve():
                issues.append(f"Missing or changed discovery: {relative}")
        for name in ("AGENTS.md", "CLAUDE.md"):
            path = project / name
            text = path.read_text() if path.is_file() else ""
            if _BEGIN not in text or _END not in text or _anchor(text, receipt["level"], True) != text:
                issues.append(f"Missing or changed instructions: {name}")
        config = _json_object(project / ".osa/config.json")
        if config.get("defaultMode") != receipt["level"]:
            issues.append("Project defaultMode differs from installation receipt")
    except (ValueError, OSError, KeyError) as error:
        issues.append(str(error))
        receipt = None
    return {"ok": not issues, "issues": issues, "receipt": receipt}
