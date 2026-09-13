"""Project file walk shared by the indexer and the freshness checker.

Yields the indexable text files under a root, skipping version-control and
build directories, oversized files, and binaries. Kept separate so `osa index`
and `osa fresh` see exactly the same set of files.
"""
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".osa", ".venv", "venv", "__pycache__",
             "dist", "build", ".next"}
SKIP_NAME_PREFIX = (".env",)
MAX_BYTES = 2_000_000


def scan(root):
    "Yield (relative posix path, Path) for each indexable file under root."
    root = Path(root)
    stack = [root]
    while stack:
        d = stack.pop()
        for entry in sorted(d.iterdir()):
            if entry.is_dir():
                if entry.name not in SKIP_DIRS:
                    stack.append(entry)
                continue
            if not entry.is_file() or entry.name.startswith(SKIP_NAME_PREFIX):
                continue
            try:
                if entry.stat().st_size > MAX_BYTES:
                    continue
                with entry.open("rb") as fh:
                    if b"\0" in fh.read(8192):
                        continue
            except OSError:
                continue
            yield entry.relative_to(root).as_posix(), entry
