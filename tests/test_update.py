"""Tests for incremental indexing: only changed files are re-extracted."""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import osa.index
from osa.index import build_graph
from osa.store import write_index
from test_provenance import GraphCase


def edge_keys(graph):
    return sorted((e["source"], e["target"], e["rel"], e["confidence"])
                  for e in graph["edges"])


class TestUpdate(GraphCase):
    def setUp(self):
        super().setUp()
        self.write("util.py", "def foo():\n    return 1\n")
        self.write("app.py", "from util import foo\n\ndef main():\n"
                             "    foo()\n")
        self.write("docs/a.md", "# A\n")

    def count_extractions(self, **kwargs):
        real = osa.index.extract_file
        with mock.patch("osa.index.extract_file", side_effect=real) as spy:
            summary = write_index(self.root, html=False, **kwargs)
        return spy.call_count, summary

    def test_first_run_writes_cache(self):
        write_index(self.root, html=False)
        cache = self.root / ".osa" / "cache" / "fragments.json"
        self.assertTrue(cache.is_file())
        self.assertIn("util.py", json.loads(cache.read_text()))

    def test_incremental_reextracts_only_changed_files(self):
        write_index(self.root, html=False)
        self.write("util.py", "def foo():\n    return 2\n\ndef bar():\n"
                              "    return 3\n")
        calls, summary = self.count_extractions(incremental=True)
        self.assertEqual(calls, 1)
        self.assertEqual(summary["extracted"], 1)

    def test_force_reextracts_everything(self):
        write_index(self.root, html=False)
        calls, _ = self.count_extractions(incremental=False)
        self.assertEqual(calls, 3)

    def test_incremental_result_matches_full_build(self):
        write_index(self.root, html=False)
        self.write("new.py", "import util\n")
        (self.root / "docs" / "a.md").unlink()
        write_index(self.root, html=False, incremental=True)
        stored = json.loads((self.root / ".osa" / "graph.json").read_text())
        full = build_graph(self.root)
        self.assertEqual(sorted(n["id"] for n in stored["nodes"]),
                         sorted(n["id"] for n in full["nodes"]))
        self.assertEqual(edge_keys(stored), edge_keys(full))

    def test_corrupt_cache_falls_back_to_full_build(self):
        write_index(self.root, html=False)
        (self.root / ".osa" / "cache" / "fragments.json").write_text("{bad")
        calls, _ = self.count_extractions(incremental=True)
        self.assertEqual(calls, 3)


if __name__ == "__main__":
    unittest.main()
