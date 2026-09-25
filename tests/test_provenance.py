"""Tests for edge provenance and Python depth in the built graph.

Every edge must say whether it was read straight from syntax (EXTRACTED) or
resolved by a heuristic (INFERRED, with a reason), and use one relation from
the closed set. Python structure (methods, inheritance, cross-file imports and
calls) must resolve to real nodes.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.index import RELATIONS, build_graph


class GraphCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def edges(self, graph, rel=None):
        return [e for e in graph["edges"] if rel is None or e["rel"] == rel]

    def has_edge(self, graph, source, target, rel, confidence=None):
        for e in graph["edges"]:
            if (e["source"], e["target"], e["rel"]) == (source, target, rel):
                return confidence is None or e["confidence"] == confidence
        return False


class TestProvenance(GraphCase):
    def test_graph_declares_schema_2(self):
        self.write("a.py", "x = 1\n")
        self.assertEqual(build_graph(self.root)["schema"], 2)

    def test_every_edge_is_labelled_and_uses_a_known_relation(self):
        self.write("util.py", "def foo():\n    return 1\n")
        self.write("app.py", "import os\nimport util\n\ndef main():\n"
                             "    util.foo()\n")
        self.write("docs/a.md", "# A\n## B\n")
        graph = build_graph(self.root)
        self.assertTrue(graph["edges"])
        for e in graph["edges"]:
            self.assertIn(e["confidence"], ("EXTRACTED", "INFERRED"), e)
            self.assertIn(e["rel"], RELATIONS, e)
            if e["confidence"] == "INFERRED":
                self.assertTrue(e.get("reason"), e)
            self.assertNotIn("resolve", e)

    def test_edges_are_deduplicated(self):
        self.write("util.py", "def foo():\n    return 1\n")
        self.write("app.py", "import util\nimport util\n")
        graph = build_graph(self.root)
        keys = [(e["source"], e["target"], e["rel"]) for e in graph["edges"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_every_edge_endpoint_is_a_node(self):
        self.write("pkg/__init__.py", "")
        self.write("pkg/core.py", "class Base:\n    pass\n")
        self.write("app.py", "from pkg.core import Base\n\n"
                             "class Child(Base):\n    def run(self):\n"
                             "        return 1\n")
        graph = build_graph(self.root)
        ids = {n["id"] for n in graph["nodes"]}
        for e in graph["edges"]:
            self.assertIn(e["source"], ids, e)
            self.assertIn(e["target"], ids, e)


class TestPythonDepth(GraphCase):
    def test_method_is_tied_to_its_class(self):
        self.write("m.py", "class A:\n    def run(self):\n        return 1\n")
        graph = build_graph(self.root)
        ids = {n["id"] for n in graph["nodes"]}
        self.assertIn("m.py::A.run", ids)
        self.assertTrue(self.has_edge(graph, "m.py::A.run", "m.py::A",
                                      "method_of", "EXTRACTED"))

    def test_same_file_inheritance(self):
        self.write("m.py", "class A:\n    pass\n\nclass B(A):\n    pass\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "m.py::B", "m.py::A",
                                      "inherits", "EXTRACTED"))

    def test_inheritance_through_import(self):
        self.write("pkg/__init__.py", "")
        self.write("pkg/core.py", "class Base:\n    pass\n")
        self.write("app.py", "from pkg.core import Base\n\n"
                             "class Child(Base):\n    pass\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "app.py::Child",
                                      "pkg/core.py::Base", "inherits",
                                      "EXTRACTED"))

    def test_relative_import_resolves_to_file(self):
        self.write("pkg/__init__.py", "")
        self.write("pkg/context.py", "def build():\n    return 1\n")
        self.write("pkg/cli.py", "from .context import build\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "pkg/cli.py", "pkg/context.py",
                                      "imports", "EXTRACTED"))

    def test_from_dot_import_submodule_resolves_to_file(self):
        self.write("pkg/__init__.py", "")
        self.write("pkg/generic.py", "x = 1\n")
        self.write("pkg/reg.py", "from . import generic\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "pkg/reg.py", "pkg/generic.py",
                                      "imports", "EXTRACTED"))

    def test_absolute_dotted_import_resolves_to_file(self):
        self.write("osa/__init__.py", "")
        self.write("osa/cli.py", "def main():\n    return 0\n")
        self.write("run.py", "from osa.cli import main\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "run.py", "osa/cli.py",
                                      "imports", "EXTRACTED"))
        self.assertFalse(self.has_edge(graph, "run.py", "osa", "imports"))

    def test_external_import_stays_a_module_node(self):
        self.write("a.py", "import json\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "a.py", "json", "imports",
                                      "EXTRACTED"))
        kinds = {n["id"]: n["kind"] for n in graph["nodes"]}
        self.assertEqual(kinds["json"], "module")

    def test_unique_stem_fallback_is_inferred(self):
        # src layout: the import name does not map to a path from the root,
        # but exactly one local file has that stem.
        self.write("src/util.py", "x = 1\n")
        self.write("app.py", "import util\n")
        graph = build_graph(self.root)
        edge = [e for e in self.edges(graph, "imports")
                if e["source"] == "app.py"][0]
        self.assertEqual(edge["target"], "src/util.py")
        self.assertEqual(edge["confidence"], "INFERRED")
        self.assertEqual(edge["reason"], "unique stem")

    def test_call_through_from_import_is_extracted(self):
        self.write("util.py", "def foo():\n    return 1\n")
        self.write("app.py", "from util import foo\n\ndef main():\n"
                             "    foo()\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "app.py::main", "util.py::foo",
                                      "calls", "EXTRACTED"))

    def test_call_through_module_attribute_is_extracted(self):
        self.write("util.py", "def foo():\n    return 1\n")
        self.write("app.py", "import util\n\ndef main():\n    util.foo()\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "app.py::main", "util.py::foo",
                                      "calls", "EXTRACTED"))

    def test_bare_call_unique_project_wide_is_inferred(self):
        self.write("util.py", "def helper_only_here():\n    return 1\n")
        self.write("app.py", "def main():\n    helper_only_here()\n")
        graph = build_graph(self.root)
        edge = [e for e in self.edges(graph, "calls")
                if e["source"] == "app.py::main"][0]
        self.assertEqual(edge["target"], "util.py::helper_only_here")
        self.assertEqual(edge["confidence"], "INFERRED")
        self.assertEqual(edge["reason"], "unique name project-wide")

    def test_builtin_call_is_never_inferred(self):
        self.write("util.py", "def len(x):\n    return 0\n")
        self.write("app.py", "def main():\n    len([])\n")
        graph = build_graph(self.root)
        calls = [e for e in self.edges(graph, "calls")
                 if e["source"] == "app.py::main"]
        self.assertEqual(calls, [])

    def test_ambiguous_bare_call_is_dropped(self):
        self.write("a.py", "def dup():\n    return 1\n")
        self.write("b.py", "def dup():\n    return 2\n")
        self.write("app.py", "def main():\n    dup()\n")
        graph = build_graph(self.root)
        calls = [e for e in self.edges(graph, "calls")
                 if e["source"] == "app.py::main"]
        self.assertEqual(calls, [])

    def test_method_call_on_self_resolves_within_class(self):
        self.write("m.py", "class A:\n    def a(self):\n        self.b()\n"
                           "    def b(self):\n        return 1\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "m.py::A.a", "m.py::A.b",
                                      "calls", "EXTRACTED"))


class TestIndexErrors(GraphCase):
    def test_unparseable_file_is_kept_and_recorded(self):
        self.write("bad.py", "def broken(:\n")
        self.write("ok.py", "x = 1\n")
        graph = build_graph(self.root)
        self.assertIn("bad.py", {n["id"] for n in graph["nodes"]})
        self.assertEqual([e["path"] for e in graph["errors"]], ["bad.py"])
        self.assertEqual(graph["errors"][0]["error"], "SyntaxError")

    def test_clean_project_has_no_errors(self):
        self.write("ok.py", "x = 1\n")
        self.assertEqual(build_graph(self.root)["errors"], [])


class TestManualEdges(GraphCase):
    def test_manual_edges_merge_as_inferred_with_evidence(self):
        self.write("a.py", "x = 1\n")
        self.write("b.py", "y = 1\n")
        edge = {"from": "a.py", "rel": "configures", "to": "b.py",
                "seen": "2026-09-25", "evidence": "a.py:1 sets b"}
        self.write(".osa/graph/edges.jsonl", json.dumps(edge) + "\n")
        graph = build_graph(self.root)
        merged = [e for e in graph["edges"] if e.get("origin") == "manual"]
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["source"], "a.py")
        self.assertEqual(merged[0]["target"], "b.py")
        self.assertEqual(merged[0]["rel"], "configures")
        self.assertEqual(merged[0]["confidence"], "INFERRED")
        self.assertEqual(merged[0]["reason"], "a.py:1 sets b")

    def test_manual_edge_to_missing_file_is_skipped(self):
        self.write("a.py", "x = 1\n")
        edge = {"from": "a.py", "rel": "tests", "to": "gone.py",
                "evidence": "old"}
        self.write(".osa/graph/edges.jsonl", json.dumps(edge) + "\nnot json\n")
        graph = build_graph(self.root)
        self.assertEqual([e for e in graph["edges"]
                          if e.get("origin") == "manual"], [])


if __name__ == "__main__":
    unittest.main()
