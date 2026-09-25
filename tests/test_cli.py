"""Tests for the osa command-line interface (osa/cli.py)."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.cli import main


def run(argv):
    "Invoke the CLI, returning (exit_code, stdout)."
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = main(argv)
    return code, buf.getvalue()


class TestCli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "cli.py").write_text("import os\n\ndef run():\n    return 1\n")

    def tearDown(self):
        self._tmp.cleanup()

    def test_index_builds_the_graph_and_reports(self):
        code, out = run(["index", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("nodes", out)
        self.assertTrue((self.root / ".osa" / "graph.json").is_file())

    def test_index_writes_and_announces_html(self):
        code, out = run(["index", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("graph.html", out)
        self.assertTrue((self.root / ".osa" / "graph.html").is_file())

    def test_brief_prints_the_directive(self):
        code, out = run(["brief"])
        self.assertEqual(code, 0)
        self.assertIn("ONE SKILL ARMY ACTIVE", out)

    def test_version_prints_a_semver(self):
        import re
        code, out = run(["version"])
        self.assertEqual(code, 0)
        self.assertRegex(out.strip(), r"\d+\.\d+\.\d+")

    def test_fresh_returns_zero_when_fresh(self):
        run(["index", str(self.root)])
        code, out = run(["fresh", str(self.root)])
        self.assertEqual(code, 0)

    def test_fresh_returns_one_when_stale(self):
        run(["index", str(self.root)])
        (self.root / "new.py").write_text("y = 2\n")
        code, out = run(["fresh", str(self.root)])
        self.assertEqual(code, 1)

    def test_fresh_auto_reindexes_and_returns_zero(self):
        run(["index", str(self.root)])
        (self.root / "new.py").write_text("y = 2\n")
        code, out = run(["fresh", str(self.root), "--auto"])
        self.assertEqual(code, 0)

    def test_context_prints_a_slice(self):
        run(["index", str(self.root)])
        code, out = run(["context", "run", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("cli.py", out)

    def test_explain_prints_a_role_summary(self):
        run(["index", str(self.root)])
        code, out = run(["explain", "cli.py", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("cli.py", out)

    def test_path_prints_route_or_no_path(self):
        run(["index", str(self.root)])
        code, out = run(["path", "cli.py", "cli.py::run", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("cli.py", out)

    def test_query_answers_with_subgraph(self):
        run(["index", str(self.root)])
        code, out = run(["query", "where is run", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("cli.py::run", out)

    def test_query_json(self):
        import json
        run(["index", str(self.root)])
        code, out = run(["query", "run", "--json", "--budget", "500",
                         "--depth", "1", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("cli.py::run", json.loads(out)["nodes"])

    def test_explain_shows_relations(self):
        run(["index", str(self.root)])
        code, out = run(["explain", "run", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("defines", out)
        self.assertIn("[E]", out)

    def test_explain_ambiguous_lists_candidates_and_exits_2(self):
        (self.root / "other.py").write_text("def run():\n    return 2\n")
        run(["index", str(self.root)])
        code, out = run(["explain", "run", "--path", str(self.root)])
        self.assertEqual(code, 2)
        self.assertIn("cli.py::run", out)
        self.assertIn("other.py::run", out)

    def test_explain_missing_exits_1(self):
        run(["index", str(self.root)])
        code, _ = run(["explain", "nothing_here", "--path", str(self.root)])
        self.assertEqual(code, 1)

    def test_path_shows_relation_per_hop(self):
        run(["index", str(self.root)])
        code, out = run(["path", "cli.py", "run", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("defines", out)

    def test_affected_lists_dependents(self):
        (self.root / "app.py").write_text("from cli import run\n\n"
                                          "def go():\n    run()\n")
        run(["index", str(self.root)])
        code, out = run(["affected", "cli.py", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("app.py::go", out)

    def test_god_nodes(self):
        run(["index", str(self.root)])
        code, out = run(["god-nodes", "--top", "1", "--json",
                         "--path", str(self.root)])
        self.assertEqual(code, 0)
        import json
        self.assertEqual(len(json.loads(out)), 1)

    def test_update_incremental_and_no_viz(self):
        run(["index", str(self.root)])
        (self.root / "cli.py").write_text("def run():\n    return 2\n")
        code, out = run(["update", str(self.root), "--no-viz"])
        self.assertEqual(code, 0)
        self.assertIn("1 re-extracted", out)

    def test_index_accepts_no_viz(self):
        code, _ = run(["index", str(self.root), "--no-viz"])
        self.assertEqual(code, 0)
        self.assertFalse((self.root / ".osa" / "graph.html").exists())

    def test_export_graphml_writes_file(self):
        run(["index", str(self.root)])
        code, out = run(["export", "graphml", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertTrue((self.root / ".osa" / "graph.graphml").is_file())

    def test_export_html_writes_file(self):
        run(["index", str(self.root)])
        code, out = run(["export", "html", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertTrue((self.root / ".osa" / "graph.html").is_file())


if __name__ == "__main__":
    unittest.main()
