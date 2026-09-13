"""Freshness tracking: know which files changed since the last index.

Keeps a sha256 baseline of the working tree in .osa/manifest.json so the engine
can reindex only what changed instead of rescanning everything, and so an
adapter can decide whether to refresh the graph at session start.
"""
import hashlib
import json
from pathlib import Path

from .scan import scan

MANIFEST_VERSION = 1


def _manifest_path(root):
    return Path(root) / ".osa" / "manifest.json"


def snapshot(root):
    "Return {rel_path: {sha256, mtime, size}} for every indexable file."
    out = {}
    for rel, path in scan(root):
        try:
            data = path.read_bytes()
            stat = path.stat()
        except OSError:
            continue
        out[rel] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "mtime": stat.st_mtime,
            "size": len(data),
        }
    return out


def write_manifest(root, files=None):
    "Write the current snapshot to .osa/manifest.json and return it."
    files = snapshot(root) if files is None else files
    mp = _manifest_path(root)
    mp.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": MANIFEST_VERSION, "files": files}
    mp.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return files


def load_manifest(root):
    "Return the stored manifest files dict, or None when not indexed yet."
    mp = _manifest_path(root)
    if not mp.is_file():
        return None
    try:
        return json.loads(mp.read_text()).get("files", {})
    except (OSError, ValueError):
        return None


def check(root):
    "Compare disk against the manifest; report added/modified/deleted/fresh."
    old = load_manifest(root)
    cur = snapshot(root)
    if old is None:
        return {"fresh": False, "manifest": None,
                "added": sorted(cur), "modified": [], "deleted": []}
    added = sorted(set(cur) - set(old))
    deleted = sorted(set(old) - set(cur))
    modified = sorted(p for p in set(cur) & set(old)
                      if cur[p]["sha256"] != old[p]["sha256"])
    return {
        "fresh": not (added or modified or deleted),
        "manifest": True,
        "added": added,
        "modified": modified,
        "deleted": deleted,
    }
