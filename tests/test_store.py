"""Tests for index persistence (osa/store.py)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.store import write_index, load_graph


class TestStore(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "cli.py").write_text("import os\n\ndef run():\n    return 1\n")

    def tearDown(self):
        self._tmp.cleanup()

    def test_write_index_creates_the_artifacts(self):
        write_index(self.root)
        self.assertTrue((self.root / ".osa" / "graph.json").is_file())
        self.assertTrue((self.root / ".osa" / "context.md").is_file())
        self.assertTrue((self.root / ".osa" / "manifest.json").is_file())
        self.assertTrue((self.root / ".osa" / "graph.html").is_file())

    def test_write_index_html_is_self_contained(self):
        write_index(self.root)
        html = (self.root / ".osa" / "graph.html").read_text()
        self.assertIn("cli.py", html)
        self.assertNotIn("https://", html)

    def test_write_index_can_skip_html(self):
        write_index(self.root, html=False)
        self.assertFalse((self.root / ".osa" / "graph.html").is_file())

    def test_graph_json_parses_and_has_nodes(self):
        write_index(self.root)
        data = json.loads((self.root / ".osa" / "graph.json").read_text())
        self.assertTrue(len(data["nodes"]) > 0)

    def test_load_graph_round_trips(self):
        write_index(self.root)
        graph = load_graph(self.root)
        self.assertIn("cli.py", {n["id"] for n in graph["nodes"]})

    def test_write_index_returns_counts(self):
        summary = write_index(self.root)
        self.assertIn("nodes", summary)
        self.assertGreater(summary["nodes"], 0)


if __name__ == "__main__":
    unittest.main()
