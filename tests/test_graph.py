"""Tests for graph ranking (osa/graph.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.graph import degree, god_nodes, entrypoints


def make_graph():
    # hub is touched by three edges; leaf_a/leaf_b/util once or twice.
    nodes = [
        {"id": "hub.py", "kind": "file", "name": "hub.py"},
        {"id": "leaf_a.py", "kind": "file", "name": "leaf_a.py"},
        {"id": "leaf_b.py", "kind": "file", "name": "leaf_b.py"},
        {"id": "util.py", "kind": "file", "name": "util.py"},
        {"id": "cli.py", "kind": "file", "name": "cli.py"},
    ]
    edges = [
        {"source": "leaf_a.py", "target": "hub.py", "rel": "imports"},
        {"source": "leaf_b.py", "target": "hub.py", "rel": "imports"},
        {"source": "hub.py", "target": "util.py", "rel": "imports"},
    ]
    return {"nodes": nodes, "edges": edges}


class TestGraphRanking(unittest.TestCase):
    def test_degree_counts_edges_touching_a_node(self):
        d = degree(make_graph())
        self.assertEqual(d["hub.py"], 3)
        self.assertEqual(d["util.py"], 1)
        self.assertEqual(d["cli.py"], 0)

    def test_god_nodes_are_ranked_by_degree_descending(self):
        top = god_nodes(make_graph(), limit=2)
        self.assertEqual(top[0], "hub.py")
        self.assertEqual(len(top), 2)

    def test_entrypoints_detects_cli_by_name(self):
        eps = entrypoints(make_graph())
        self.assertIn("cli.py", eps)
        self.assertNotIn("leaf_a.py", eps)


if __name__ == "__main__":
    unittest.main()
