#!/usr/bin/env python3
"""Bundle the osa engine into a single runnable file that ships with the skills.

Produces skills/one-skill-army/osa.pyz, a standard-library zipapp. Run it
anywhere with `python3 osa.pyz <command>`, no install and no PYTHONPATH setup,
so the engine travels with `cp -r skills/*`. Rebuild after changing anything
under osa/:

    python3 scripts/build-osa.py
"""
import shutil
import tempfile
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "osa"
DEFAULT_OUT = ROOT / "skills" / "one-skill-army" / "osa.pyz"


def build(out=DEFAULT_OUT):
    "Stage the osa package with an entry point and write the zipapp to `out`."
    out = Path(out)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        shutil.copytree(SRC, stage / "osa",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (stage / "__main__.py").write_text(
            "import sys\nfrom osa.cli import main\nsys.exit(main())\n",
            encoding="utf-8")
        out.parent.mkdir(parents=True, exist_ok=True)
        zipapp.create_archive(stage, out, interpreter="/usr/bin/env python3")
    return out


if __name__ == "__main__":
    print("built", build())
