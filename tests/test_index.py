"""Tests for the project graph builder (osa/index.py)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.index import build_graph


class TestBuildGraph(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def ids(self, graph):
        return {n["id"] for n in graph["nodes"]}

    def test_merges_symbols_and_files_across_the_project(self):
        self.write("pkg/mod.py", "import os\n\ndef greet():\n    return 1\n")
        self.write("docs/g.md", "# Title\n")
        graph = build_graph(self.root)
        ids = self.ids(graph)
        self.assertIn("pkg/mod.py", ids)
        self.assertIn("pkg/mod.py::greet", ids)
        self.assertIn("os", ids)
        self.assertIn("docs/g.md", ids)
        self.assertIn("docs/g.md#Title", ids)

    def test_node_ids_are_unique(self):
        self.write("a.py", "import os\n")
        self.write("b.py", "import os\n")
        graph = build_graph(self.root)
        ids = [n["id"] for n in graph["nodes"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_skips_ignored_directories(self):
        self.write(".git/config.py", "def secret():\n    return 1\n")
        self.write("real.py", "def keep():\n    return 1\n")
        ids = self.ids(build_graph(self.root))
        self.assertIn("real.py", ids)
        self.assertNotIn(".git/config.py", ids)

    def test_uses_posix_relative_paths(self):
        self.write("pkg/sub/deep.py", "x = 1\n")
        ids = self.ids(build_graph(self.root))
        self.assertIn("pkg/sub/deep.py", ids)

    def test_resolves_internal_import_to_the_local_file(self):
        self.write("util.py", "def foo():\n    return 1\n")
        self.write("app.py", "import util\n")
        graph = build_graph(self.root)
        imports = [e for e in graph["edges"] if e["rel"] == "imports"]
        self.assertIn(
            {"source": "app.py", "target": "util.py", "rel": "imports"},
            imports,
        )

    def test_ambiguous_stem_is_not_resolved(self):
        # Two files share a stem: resolving would be a guess, so leave the
        # import as an external module node rather than invent a target.
        self.write("a/util.py", "x = 1\n")
        self.write("b/util.py", "x = 1\n")
        self.write("app.py", "import util\n")
        imports = [e for e in build_graph(self.root)["edges"]
                   if e["rel"] == "imports"]
        self.assertIn(
            {"source": "app.py", "target": "util", "rel": "imports"},
            imports,
        )


if __name__ == "__main__":
    unittest.main()
