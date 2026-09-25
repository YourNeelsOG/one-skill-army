"""Tests for JavaScript / TypeScript extraction through the table engine."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.extractors import extract_file
from test_provenance import GraphCase

from osa.index import build_graph


def kinds(result):
    return {n["id"]: n["kind"] for n in result["nodes"]}


class TestJsDefinitions(unittest.TestCase):
    def test_functions_classes_and_types(self):
        src = ("export function load() {}\n"
               "export default class Store {}\n"
               "const add = (a, b) => a + b;\n"
               "export const run = async () => {\n  return 1;\n};\n"
               "interface Shape { area(): number }\n"
               "export type Id = string;\n"
               "enum Color { Red }\n")
        k = kinds(extract_file("src/a.ts", src))
        self.assertEqual(k["src/a.ts::load"], "function")
        self.assertEqual(k["src/a.ts::Store"], "class")
        self.assertEqual(k["src/a.ts::add"], "function")
        self.assertEqual(k["src/a.ts::run"], "function")
        self.assertEqual(k["src/a.ts::Shape"], "interface")
        self.assertEqual(k["src/a.ts::Id"], "type")
        self.assertEqual(k["src/a.ts::Color"], "enum")

    def test_class_methods_are_tied_to_class(self):
        src = ("class Store {\n  constructor(x) { this.x = x; }\n"
               "  async save(item) {\n    if (item) { return 1; }\n  }\n"
               "  static of() { return new Store(); }\n}\n"
               "if (ready) {\n  go();\n}\n")
        result = extract_file("a.js", src)
        k = kinds(result)
        self.assertEqual(k["a.js::Store.save"], "method")
        self.assertEqual(k["a.js::Store.of"], "method")
        self.assertNotIn("a.js::Store.if", k)
        self.assertNotIn("a.js::if", k)
        edges = {(e["source"], e.get("target"), e["rel"])
                 for e in result["edges"]}
        self.assertIn(("a.js::Store.save", "a.js::Store", "method_of"), edges)

    def test_commented_and_string_code_is_ignored(self):
        src = ("// function ghost() {}\n"
               "const s = 'import x from \"./nope\"';\n"
               "/* class Hidden {} */\n")
        result = extract_file("a.js", src)
        self.assertEqual([n["id"] for n in result["nodes"]], ["a.js"])
        self.assertEqual(result["edges"], [])

    def test_line_numbers(self):
        result = extract_file("a.js", "\n\nfunction third() {}\n")
        node = [n for n in result["nodes"] if n["kind"] == "function"][0]
        self.assertEqual(node["line"], 3)


class TestJsGraph(GraphCase):
    def test_relative_imports_resolve_with_extension_probe(self):
        self.write("src/util.ts", "export function f() {}\n")
        self.write("src/lib/index.js", "export const x = 1;\n")
        self.write("src/app.tsx",
                   "import { f } from './util';\n"
                   "import lib from \"./lib\";\n"
                   "const m = require('./util');\n"
                   "import React from 'react';\n"
                   "import { y } from '@scope/pkg/deep';\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "src/app.tsx", "src/util.ts",
                                      "imports", "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "src/app.tsx",
                                      "src/lib/index.js", "imports",
                                      "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "src/app.tsx", "react",
                                      "imports", "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "src/app.tsx", "@scope/pkg",
                                      "imports", "EXTRACTED"))

    def test_multiline_import_and_reexport(self):
        self.write("b.ts", "export const q = 1;\n")
        self.write("c.ts", "export const r = 1;\n")
        self.write("a.ts", "import {\n  q,\n} from './b';\n"
                           "export * from './c';\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "a.ts", "b.ts", "imports"))
        self.assertTrue(self.has_edge(graph, "a.ts", "c.ts", "imports"))

    def test_missing_relative_import_is_dropped(self):
        self.write("a.ts", "import x from './gone';\n")
        graph = build_graph(self.root)
        self.assertEqual(self.edges(graph, "imports"), [])

    def test_extends_and_implements(self):
        self.write("base.ts", "export class Base {}\n"
                              "export interface Named {}\n")
        self.write("a.ts", "import { Base } from './base';\n"
                           "class Local {}\n"
                           "class Child extends Local {}\n"
                           "class Other extends Base implements Named {}\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "a.ts::Child", "a.ts::Local",
                                      "inherits", "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "a.ts::Other", "base.ts::Base",
                                      "inherits", "INFERRED"))
        self.assertTrue(self.has_edge(graph, "a.ts::Other", "base.ts::Named",
                                      "inherits", "INFERRED"))


if __name__ == "__main__":
    unittest.main()
