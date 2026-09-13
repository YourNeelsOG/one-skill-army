"""Tests for graph insight helpers (osa/analyze.py, part 2)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.analyze import (communities, surprising_connections,
                         suggested_questions, shortest_path, explain)


def two_triangles():
    nodes = [{"id": n, "kind": "file", "name": n}
             for n in ("a", "b", "c", "x", "y", "z")]
    edges = [
        {"source": "a", "target": "b", "rel": "imports"},
        {"source": "b", "target": "c", "rel": "imports"},
        {"source": "c", "target": "a", "rel": "imports"},
        {"source": "x", "target": "y", "rel": "imports"},
        {"source": "y", "target": "z", "rel": "imports"},
        {"source": "z", "target": "x", "rel": "imports"},
        {"source": "c", "target": "x", "rel": "imports"},
    ]
    return {"nodes": nodes, "edges": edges}


class TestInsights(unittest.TestCase):
    def test_surprising_connections_are_cross_community_edges(self):
        g = two_triangles()
        comm = communities(g)
        surprises = surprising_connections(g, comm)
        pairs = {tuple(sorted((s["source"], s["target"]))) for s in surprises}
        self.assertIn(("c", "x"), pairs)          # the bridge is surprising
        self.assertNotIn(("a", "b"), pairs)       # intra-community is not

    def test_surprising_connections_ignore_structural_edges(self):
        # A defines/contains edge is parent-child structure, never "surprising".
        g = {"nodes": [{"id": "f.py", "kind": "file", "name": "f.py"},
                       {"id": "f.py::x", "kind": "function", "name": "x"}],
             "edges": [{"source": "f.py", "target": "f.py::x",
                        "rel": "defines"}]}
        comm = communities(g)
        self.assertEqual(surprising_connections(g, comm), [])

    def test_suggested_questions_mention_a_bridge_node(self):
        g = two_triangles()
        qs = suggested_questions(g, communities(g))
        joined = " ".join(qs).lower()
        self.assertTrue(qs)
        self.assertTrue("c" in joined or "x" in joined)

    def test_shortest_path_finds_a_route(self):
        self.assertEqual(shortest_path(two_triangles(), "a", "y")[0], "a")
        self.assertEqual(shortest_path(two_triangles(), "a", "y")[-1], "y")

    def test_shortest_path_returns_empty_when_disconnected(self):
        g = {"nodes": [{"id": "p", "kind": "file", "name": "p"},
                       {"id": "q", "kind": "file", "name": "q"}],
             "edges": []}
        self.assertEqual(shortest_path(g, "p", "q"), [])

    def test_explain_reports_role_of_a_node(self):
        info = explain(two_triangles(), "c")
        self.assertEqual(info["id"], "c")
        self.assertEqual(info["degree"], 3)
        self.assertIn("community", info)
        self.assertIn("summary", info)


if __name__ == "__main__":
    unittest.main()
