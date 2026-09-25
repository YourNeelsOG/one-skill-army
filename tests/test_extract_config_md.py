"""Tests for config (JSON/YAML/TOML) and Markdown extraction."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.extractors import extract_file
from osa.index import build_graph
from test_provenance import GraphCase


class TestConfig(GraphCase):
    def test_json_top_level_keys_become_nodes(self):
        result = extract_file("conf/app.json",
                              json.dumps({"server": {"port": 1}, "name": "x"}))
        ids = {n["id"]: n["kind"] for n in result["nodes"]}
        self.assertEqual(ids["conf/app.json#server"], "heading")
        self.assertEqual(ids["conf/app.json#name"], "heading")

    def test_invalid_json_keeps_file_node(self):
        result = extract_file("bad.json", "{not json")
        self.assertEqual([n["id"] for n in result["nodes"]], ["bad.json"])

    def test_package_json_dependencies_are_imports(self):
        self.write("package.json", json.dumps({
            "dependencies": {"react": "^18"},
            "devDependencies": {"@types/node": "^20"},
            "scripts": {"build": "node scripts/build.js"}}))
        self.write("scripts/build.js", "console.log(1);\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "package.json", "react",
                                      "imports", "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "package.json", "@types/node",
                                      "imports", "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "package.json",
                                      "scripts/build.js", "references",
                                      "INFERRED"))

    def test_yaml_keys_and_path_references(self):
        self.write("scripts/test.sh", "echo ok\n")
        self.write(".ci/pipeline.yml",
                   "name: ci\n# job: scripts/ghost.sh\n"
                   "jobs:\n  test:\n    run: bash scripts/test.sh\n"
                   "    url: https://example.com/a/b.sh\n")
        graph = build_graph(self.root)
        ids = {n["id"] for n in graph["nodes"]}
        self.assertIn(".ci/pipeline.yml#jobs", ids)
        self.assertIn(".ci/pipeline.yml#name", ids)
        self.assertTrue(self.has_edge(graph, ".ci/pipeline.yml",
                                      "scripts/test.sh", "references",
                                      "INFERRED"))
        targets = {e["target"] for e in graph["edges"]}
        self.assertNotIn("scripts/ghost.sh", targets)

    def test_toml_tables_and_cargo_dependencies(self):
        self.write("Cargo.toml", "[package]\nname = \"app\"\n\n"
                                 "[dependencies]\nserde = \"1\"\n"
                                 "tokio = { version = \"1\" }\n")
        graph = build_graph(self.root)
        ids = {n["id"] for n in graph["nodes"]}
        self.assertIn("Cargo.toml#package", ids)
        self.assertTrue(self.has_edge(graph, "Cargo.toml", "serde",
                                      "imports", "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "Cargo.toml", "tokio",
                                      "imports", "EXTRACTED"))

    def test_pyproject_dependencies(self):
        self.write("pyproject.toml",
                   "[project]\nname = \"x\"\n"
                   "dependencies = [\"requests>=2\", \"click[extra]\"]\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "pyproject.toml", "requests",
                                      "imports", "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "pyproject.toml", "click",
                                      "imports", "EXTRACTED"))


class TestMarkdown(GraphCase):
    def test_headings_nest(self):
        src = "# Top\n## Mid\n### Low\n## Mid2\n"
        edges = {(e["source"], e["target"])
                 for e in extract_file("d.md", src)["edges"]}
        self.assertIn(("d.md", "d.md#Top"), edges)
        self.assertIn(("d.md#Top", "d.md#Mid"), edges)
        self.assertIn(("d.md#Mid", "d.md#Low"), edges)
        self.assertIn(("d.md#Top", "d.md#Mid2"), edges)
        self.assertNotIn(("d.md", "d.md#Low"), edges)

    def test_heading_inside_code_fence_is_ignored(self):
        src = "# Real\n```\n# not a heading\n```\n"
        ids = [n["id"] for n in extract_file("d.md", src)["nodes"]]
        self.assertEqual(ids, ["d.md", "d.md#Real"])

    def test_links_and_at_mentions_resolve_to_files(self):
        self.write("AGENTS.md", "# Rules\n")
        self.write("docs/guide.md", "# Guide\n")
        self.write("skills/x/SKILL.md", "# X\n")
        self.write("CLAUDE.md",
                   "@AGENTS.md\n"
                   "See [guide](docs/guide.md#install) and "
                   "[site](https://example.com/docs/guide.md).\n"
                   "Mail me@example.com. `[fake](skills/x/SKILL.md)`\n"
                   "Missing [gone](nope.md).\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "CLAUDE.md", "AGENTS.md",
                                      "links_to", "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "CLAUDE.md", "docs/guide.md",
                                      "links_to", "EXTRACTED"))
        links = {e["target"] for e in self.edges(graph, "links_to")}
        self.assertEqual(links, {"AGENTS.md", "docs/guide.md"})


if __name__ == "__main__":
    unittest.main()
