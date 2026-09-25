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


def data_of(html):
    "Parse the JSON data block embedded in the HTML view."
    import json
    start = html.index("const DATA = ") + len("const DATA = ")
    end = html.index(";\n", start)
    return json.loads(html[start:end].replace("<\\/", "</"))


def rich_graph():
    return {
        "nodes": [{"id": "a.py", "kind": "file", "name": "a.py", "path": "a.py",
                   "line": 1},
                  {"id": "b.py", "kind": "file", "name": "b.py", "path": "b.py",
                   "line": 1},
                  {"id": "a.py::run", "kind": "function", "name": "run",
                   "path": "a.py", "line": 3}],
        "edges": [{"source": "a.py", "target": "a.py::run", "rel": "defines",
                   "confidence": "EXTRACTED"},
                  {"source": "a.py", "target": "b.py", "rel": "imports",
                   "confidence": "INFERRED", "reason": "unique stem"}],
    }


class TestGraphmlConfidence(unittest.TestCase):
    def test_graphml_edges_carry_confidence(self):
        xml = to_graphml(rich_graph())
        minidom.parseString(xml)
        self.assertIn('<data key="confidence">INFERRED</data>', xml)


class TestHtmlView(unittest.TestCase):
    def test_edges_carry_relation_and_confidence(self):
        data = data_of(to_html(rich_graph()))
        self.assertEqual({(e["rel"], e["conf"]) for e in data["edges"]},
                         {("defines", "E"), ("imports", "I")})

    def test_inferred_edges_are_drawn_dashed(self):
        self.assertIn("setLineDash", to_html(rich_graph()))

    def test_has_legend_side_panel_search_and_color_toggle(self):
        html = to_html(rich_graph())
        for element in ('id="legend"', 'id="panel"', 'id="q"',
                        'id="colorby"'):
            self.assertIn(element, html)

    def test_nodes_carry_community_and_labels_exist(self):
        data = data_of(to_html(rich_graph()))
        self.assertTrue(all("c" in n for n in data["nodes"]))
        self.assertTrue(data["labels"])

    def test_big_graph_starts_with_symbols_hidden(self):
        big = {"nodes": [{"id": "f" + str(i), "kind": "function",
                          "name": "f"} for i in range(1600)], "edges": []}
        self.assertTrue(data_of(to_html(big))["hideSymbols"])
        self.assertFalse(data_of(to_html(rich_graph()))["hideSymbols"])

    def test_physics_stays_finite_and_cools_down(self):
        import shutil
        import subprocess
        if not shutil.which("node"):
            self.skipTest("node not installed")
        html = to_html(rich_graph())
        physics = html[html.index("function tick("):html.index("function draw(")]
        harness = (
            "let W=800,H=600,alpha=1;const nodes=[];const links=[];\n"
            "for(let i=0;i<300;i++)nodes.push({x:(i*37)%800,y:(i*91)%600,"
            "vx:0,vy:0,show:true});\n"
            "for(let i=1;i<300;i++)links.push({s:i,t:(i*7)%i,show:true});\n"
            + physics +
            "let steps=0;while(alpha>ALPHA_MIN&&steps<5000){tick();steps++;}\n"
            "const ok=nodes.every(n=>Number.isFinite(n.x)&&Number.isFinite(n.y));"
            "console.log(JSON.stringify({ok,steps}));")
        out = subprocess.run(["node", "-e", harness], capture_output=True,
                             text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        result = __import__("json").loads(out.stdout)
        self.assertTrue(result["ok"])
        self.assertLess(result["steps"], 5000)


if __name__ == "__main__":
    unittest.main()
