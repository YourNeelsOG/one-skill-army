"""The shipped osa.pyz zipapp builds and runs standalone (no PYTHONPATH)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import importlib.util

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "build_osa", ROOT / "scripts" / "build-osa.py")
build_osa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_osa)


class TestPyz(unittest.TestCase):
    def test_builds_and_runs_without_pythonpath(self):
        with tempfile.TemporaryDirectory() as tmp:
            pyz = Path(tmp) / "osa.pyz"
            build_osa.build(out=pyz)
            self.assertTrue(pyz.is_file())

            proj = Path(tmp) / "proj"
            proj.mkdir()
            (proj / "app.py").write_text("def run():\n    return 1\n")

            # Run with an empty environment for imports: proves no PYTHONPATH
            # or repo checkout is needed, only the single .pyz file.
            result = subprocess.run(
                [sys.executable, str(pyz), "index", str(proj)],
                capture_output=True, text=True, cwd=tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((proj / ".osa" / "graph.json").is_file())

    def test_shipped_pyz_exists(self):
        self.assertTrue((ROOT / "skills" / "one-skill-army" / "osa.pyz").is_file())

    def test_shipped_pyz_matches_source(self):
        # Guard against a stale committed pyz: every osa source file must be
        # embedded byte-for-byte. If this fails, run scripts/build-osa.py.
        import zipfile
        pyz = ROOT / "skills" / "one-skill-army" / "osa.pyz"
        with zipfile.ZipFile(pyz) as z:
            names = set(z.namelist())
            for src in sorted((ROOT / "osa").rglob("*.py")):
                rel = "osa/" + src.relative_to(ROOT / "osa").as_posix()
                self.assertIn(rel, names, rel + " missing (rebuild osa.pyz)")
                self.assertEqual(z.read(rel), src.read_bytes(),
                                 rel + " stale in osa.pyz (rebuild it)")


if __name__ == "__main__":
    unittest.main()
