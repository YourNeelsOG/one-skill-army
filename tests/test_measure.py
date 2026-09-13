"""Tests for the measurement harness (osa/measure.py)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.measure import measure


class TestMeasure(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # A project big enough that the map is smaller than the whole tree.
        for i in range(8):
            (self.root / ("mod%d.py" % i)).write_text(
                "import os\n\n" + "\n".join(
                    "def f%d_%d():\n    return %d\n" % (i, j, j)
                    for j in range(10)))

    def tearDown(self):
        self._tmp.cleanup()

    def test_reports_token_counts_and_reduction(self):
        result = measure(self.root)
        self.assertIn("context_tokens", result)
        self.assertIn("project_tokens", result)
        self.assertIn("reduction_pct", result)

    def test_context_is_smaller_than_the_whole_project(self):
        result = measure(self.root)
        self.assertLess(result["context_tokens"], result["project_tokens"])
        self.assertGreater(result["reduction_pct"], 0)

    def test_reduction_is_a_percentage(self):
        result = measure(self.root)
        self.assertLessEqual(result["reduction_pct"], 100)
        self.assertGreaterEqual(result["reduction_pct"], 0)


if __name__ == "__main__":
    unittest.main()
