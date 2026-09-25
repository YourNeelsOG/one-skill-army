"""Tests for the full graph report (osa/report.py, .osa/GRAPH_REPORT.md)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.index import build_graph
from osa.analyze import communities
from osa.report import build_report, community_labels
from osa.store import write_index
from test_provenance import GraphCase


class TestReport(GraphCase):
    def setUp(self):
        super().setUp()
        self.write("pkg/__init__.py", "")
        self.write("pkg/core.py", "def build():\n    return 1\n")
        self.write("pkg/cli.py", "from pkg.core import build\n\n"
                                 "def main():\n    build()\n")
        self.write("src/util.py", "def helper():\n    return 1\n")
        self.write("app.py", "import util\n")  # unique stem: INFERRED
        self.write("bad.py", "def broken(:\n")
        self.write("README.md", "# Intro\nSee [core](pkg/core.py).\n")

    def test_report_has_every_section(self):
        text = build_report(build_graph(self.root))
        for heading in ("## Summary", "## Entrypoints", "## God nodes",
                        "## Bridges", "## Communities",
                        "## Surprising connections",
                        "## Inferred edges (review these)",
                        "## Index errors", "## Questions"):
            self.assertIn(heading, text)

    def test_summary_counts_relations_by_confidence(self):
        text = build_report(build_graph(self.root))
        self.assertIn("| imports | ", text)
        self.assertIn("| calls | ", text)
        self.assertIn("INFERRED", text)

    def test_inferred_edges_listed_with_reason(self):
        text = build_report(build_graph(self.root))
        self.assertIn("app.py --imports--> src/util.py (unique stem)", text)

    def test_index_errors_listed(self):
        text = build_report(build_graph(self.root))
        self.assertIn("bad.py: SyntaxError", text)

    def test_community_labels_name_directory_and_hub(self):
        graph = build_graph(self.root)
        labels = community_labels(graph, communities(graph))
        comm = communities(graph)["pkg/core.py::build"]
        self.assertIn("pkg/", labels[comm])

    def test_community_hub_is_never_an_external_module(self):
        for i in range(6):
            self.write("m" + str(i) + ".py", "import json\n")
        graph = build_graph(self.root)
        comm = communities(graph)
        label = community_labels(graph, comm)[comm["json"]]
        self.assertNotIn("(json)", label)

    def test_write_index_writes_report_and_context_points_to_it(self):
        write_index(self.root, html=False)
        osa = self.root / ".osa"
        self.assertTrue((osa / "GRAPH_REPORT.md").is_file())
        self.assertIn("GRAPH_REPORT.md", (osa / "context.md").read_text())


if __name__ == "__main__":
    unittest.main()
