"""Tests for graph exports (osa/export.py)."""
import sys
import unittest
import xml.dom.minidom as minidom
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.export import to_graphml, to_html


def graph():
    return {
        "nodes": [{"id": "a.py", "kind": "file", "name": "a.py"},
                  {"id": "a.py::run", "kind": "function", "name": "run"}],
        "edges": [{"source": "a.py", "target": "a.py::run", "rel": "defines"}],
    }


class TestExport(unittest.TestCase):
    def test_graphml_is_well_formed_xml(self):
        xml = to_graphml(graph())
        minidom.parseString(xml)  # raises if malformed
        self.assertIn("graphml", xml)

    def test_graphml_contains_nodes_and_edge(self):
        xml = to_graphml(graph())
        self.assertIn("a.py::run", xml)
        self.assertIn("<edge", xml)

    def test_html_embeds_nodes_and_is_self_contained(self):
        html = to_html(graph())
        self.assertIn("a.py", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)

    def test_html_escapes_closing_script(self):
        # A node id with </script> must be escaped in the data block, leaving
        # only the template's own single closing </script> tag.
        g = {"nodes": [{"id": "x</script>", "kind": "file", "name": "x"}],
             "edges": []}
        html = to_html(g)
        self.assertEqual(html.count("</script>"), 1)
        self.assertIn("<\\/script>", html)


if __name__ == "__main__":
    unittest.main()
