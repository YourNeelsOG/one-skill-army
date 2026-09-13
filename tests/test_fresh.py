"""Tests for freshness tracking (osa/fresh.py)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.fresh import snapshot, write_manifest, check


class TestFresh(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def test_snapshot_hashes_every_indexable_file(self):
        self.write("a.py", "x = 1\n")
        snap = snapshot(self.root)
        self.assertIn("a.py", snap)
        self.assertIn("sha256", snap["a.py"])

    def test_check_reports_fresh_after_manifest_written(self):
        self.write("a.py", "x = 1\n")
        write_manifest(self.root)
        result = check(self.root)
        self.assertTrue(result["fresh"])

    def test_check_detects_modified_file(self):
        self.write("a.py", "x = 1\n")
        write_manifest(self.root)
        self.write("a.py", "x = 2\n")
        result = check(self.root)
        self.assertFalse(result["fresh"])
        self.assertIn("a.py", result["modified"])

    def test_check_detects_added_and_deleted(self):
        self.write("a.py", "x = 1\n")
        write_manifest(self.root)
        self.write("b.py", "y = 1\n")
        (self.root / "a.py").unlink()
        result = check(self.root)
        self.assertIn("b.py", result["added"])
        self.assertIn("a.py", result["deleted"])

    def test_check_without_manifest_is_not_fresh(self):
        self.write("a.py", "x = 1\n")
        result = check(self.root)
        self.assertFalse(result["fresh"])
        self.assertIsNone(result.get("manifest"))


if __name__ == "__main__":
    unittest.main()
