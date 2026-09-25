"""Tests for graph queries (osa/query.py): resolve, query, affected, describe."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.index import build_graph
from osa.query import (affected, describe, path_hops, query, resolve_node,
                       tokenize)
from test_provenance import GraphCase


class QueryCase(GraphCase):
    def setUp(self):
        super().setUp()
        self.write("store/db.py", "class Database:\n"
                                  "    def connect(self):\n"
                                  "        return 1\n")
        self.write("api/users.py", "from store.db import Database\n\n"
                                   "def load_users():\n"
                                   "    return Database()\n")
        self.write("api/orders.py", "from api.users import load_users\n\n"
                                    "def list_orders():\n"
                                    "    return load_users()\n")
        self.write("cli.py", "from api.orders import list_orders\n\n"
                             "def main():\n    list_orders()\n")
        self.graph = build_graph(self.root)


class TestTokenize(unittest.TestCase):
    def test_splits_case_and_drops_stopwords(self):
        terms = tokenize("How does loadUsers reach the database_layer?")
        self.assertIn("load", terms)
        self.assertIn("users", terms)
        self.assertIn("database", terms)
        self.assertIn("database_layer", terms)
        self.assertNotIn("how", terms)
        self.assertNotIn("the", terms)


class TestResolve(QueryCase):
    def test_exact_id(self):
        self.assertEqual(resolve_node(self.graph, "cli.py"), ("cli.py", []))

    def test_unique_name(self):
        node, _ = resolve_node(self.graph, "load_users")
        self.assertEqual(node, "api/users.py::load_users")

    def test_case_insensitive_substring(self):
        node, _ = resolve_node(self.graph, "DATABASE.conn")
        self.assertEqual(node, "store/db.py::Database.connect")

    def test_ambiguous_returns_candidates(self):
        node, candidates = resolve_node(self.graph, "api/")
        self.assertIsNone(node)
        self.assertIn("api/users.py", candidates)
        self.assertIn("api/orders.py", candidates)

    def test_missing(self):
        self.assertEqual(resolve_node(self.graph, "nothing_like_this"),
                         (None, []))


class TestQuery(QueryCase):
    def test_question_returns_relevant_subgraph(self):
        result = query(self.graph, "how are orders connected to users?")
        self.assertIn("api/orders.py::list_orders", result["nodes"])
        self.assertIn("api/users.py::load_users", result["nodes"])
        rels = {(e["source"], e["target"], e["rel"]) for e in result["edges"]}
        self.assertIn(("api/orders.py::list_orders",
                       "api/users.py::load_users", "calls"), rels)
        self.assertIn("calls", result["text"])
        self.assertIn("[E]", result["text"])

    def test_budget_caps_output(self):
        result = query(self.graph, "users orders database", budget=40)
        self.assertLessEqual(len(result["text"]) // 4, 40)

    def test_depth_limits_reach(self):
        shallow = query(self.graph, "Database connect", depth=1)
        deep = query(self.graph, "Database connect", depth=3)
        self.assertLess(len(shallow["nodes"]), len(deep["nodes"]))

    def test_dfs_mode_runs(self):
        result = query(self.graph, "users", dfs=True)
        self.assertTrue(result["nodes"])

    def test_rare_terms_and_word_forms_rank_first(self):
        # "resolver" must reach resolve_edges, and the common word "edges"
        # (in many test names) must not outrank it.
        self.write("resolve.py", "def resolve_edges():\n    return 1\n")
        self.write("tests/test_x.py",
                   "def test_edges_a():\n    pass\n"
                   "def test_edges_b():\n    pass\n"
                   "def test_edges_c():\n    pass\n"
                   "def edges():\n    pass\n")
        graph = build_graph(self.root)
        result = query(graph, "how does the resolver build edges")
        self.assertEqual(result["seeds"][0], "resolve.py::resolve_edges")

    def test_no_match(self):
        result = query(self.graph, "zzz qqq")
        self.assertEqual(result["nodes"], [])
        self.assertIn("No node matches", result["text"])


class TestAffected(QueryCase):
    def test_reverse_dependents_of_a_file(self):
        hits = {h["id"]: h["depth"] for h in
                affected(self.graph, "store/db.py", depth=3)}
        self.assertIn("api/users.py", hits)          # imports it
        self.assertIn("api/users.py::load_users", hits)  # calls its class
        self.assertIn("api/orders.py::list_orders", hits)
        self.assertNotIn("store/db.py", hits)

    def test_depth_one(self):
        hits = {h["id"] for h in affected(self.graph,
                                           "api/users.py::load_users",
                                           depth=1)}
        self.assertEqual(hits, {"api/orders.py::list_orders"})

    def test_relation_filter(self):
        hits = {h["id"] for h in affected(self.graph, "store/db.py", depth=1,
                                          relations=["imports"])}
        self.assertEqual(hits, {"api/users.py"})


class TestDescribe(QueryCase):
    def test_groups_neighbors_by_relation_and_direction(self):
        info = describe(self.graph, "api/users.py::load_users")
        self.assertEqual(info["kind"], "function")
        self.assertIn("api/orders.py::list_orders",
                      [n["id"] for n in info["incoming"]["calls"]])
        self.assertIn("store/db.py::Database",
                      [n["id"] for n in info["outgoing"]["calls"]])
        self.assertIn("api/users.py:3", info["text"])

    def test_path_hops_carry_relation_and_confidence(self):
        hops = path_hops(self.graph, ["cli.py::main",
                                      "api/orders.py::list_orders"])
        self.assertEqual(hops[0]["rel"], "calls")
        self.assertEqual(hops[0]["confidence"], "EXTRACTED")
        self.assertEqual(hops[0]["direction"], "->")


if __name__ == "__main__":
    unittest.main()
