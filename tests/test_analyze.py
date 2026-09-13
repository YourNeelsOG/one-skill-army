"""Tests for deterministic graph analysis (osa/analyze.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.analyze import communities, betweenness, god_nodes_by_betweenness


def star():
    # center connected to three leaves; center is the only bridge.
    nodes = [{"id": n, "kind": "file", "name": n}
             for n in ("center", "a", "b", "c")]
    edges = [{"source": "center", "target": t, "rel": "imports"}
             for t in ("a", "b", "c")]
    return {"nodes": nodes, "edges": edges}


def two_triangles():
    # triangle {a,b,c} and triangle {x,y,z} joined by one edge c-x.
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


class TestAnalyze(unittest.TestCase):
    def test_betweenness_center_beats_leaves(self):
        b = betweenness(star())
        self.assertGreater(b["center"], b["a"])
        self.assertEqual(b["a"], 0.0)

    def test_betweenness_is_deterministic(self):
        self.assertEqual(betweenness(two_triangles()),
                         betweenness(two_triangles()))

    def test_god_nodes_by_betweenness_ranks_center_first(self):
        self.assertEqual(god_nodes_by_betweenness(star(), limit=1), ["center"])

    def test_communities_find_two_groups(self):
        comm = communities(two_triangles())
        # a,b,c should share a label distinct from x,y,z (join edge aside).
        self.assertEqual(len({comm["a"], comm["b"], comm["c"]}), 1)
        self.assertEqual(len({comm["x"], comm["y"], comm["z"]}), 1)
        self.assertNotEqual(comm["a"], comm["z"])

    def test_communities_deterministic(self):
        self.assertEqual(communities(two_triangles()),
                         communities(two_triangles()))


if __name__ == "__main__":
    unittest.main()
