"""Tests for the context digest and slice (osa/context.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.context import build_context, context_slice


def make_graph():
    nodes = [
        {"id": "cli.py", "kind": "file", "name": "cli.py"},
        {"id": "core.py", "kind": "file", "name": "core.py"},
        {"id": "core.py::run", "kind": "function", "name": "run",
         "path": "core.py", "line": 10},
        {"id": "helpers.py", "kind": "file", "name": "helpers.py"},
    ]
    edges = [
        {"source": "cli.py", "target": "core.py", "rel": "imports"},
        {"source": "core.py", "target": "helpers.py", "rel": "imports"},
        {"source": "core.py", "target": "core.py::run", "rel": "defines"},
    ]
    return {"nodes": nodes, "edges": edges}


class TestContext(unittest.TestCase):
    def test_digest_lists_entrypoints_and_god_nodes(self):
        text = build_context(make_graph())
        self.assertIn("cli.py", text)
        self.assertIn("core.py", text)

    def test_digest_respects_a_small_budget(self):
        text = build_context(make_graph(), budget=200)
        self.assertLessEqual(len(text), 200)

    def test_digest_includes_analysis_sections(self):
        text = build_context(make_graph(), budget=5000).lower()
        self.assertIn("central", text)
        self.assertIn("communit", text)

    def test_slice_returns_matching_node_and_its_neighbors(self):
        text = context_slice(make_graph(), "core")
        self.assertIn("core.py", text)
        # neighbors reached by an edge from/to the match
        self.assertIn("helpers.py", text)

    def test_slice_reports_when_nothing_matches(self):
        text = context_slice(make_graph(), "nonexistent_xyz")
        self.assertIn("no match", text.lower())


if __name__ == "__main__":
    unittest.main()
