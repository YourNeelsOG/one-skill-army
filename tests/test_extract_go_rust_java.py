"""Tests for Go, Rust and Java extraction through the table engine."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.extractors import extract_file
from osa.index import build_graph
from test_provenance import GraphCase


def kinds(result):
    return {n["id"]: n["kind"] for n in result["nodes"]}


class TestGo(GraphCase):
    def test_definitions_and_methods(self):
        src = ("package store\n\n"
               "type Db struct {\n\tname string\n}\n\n"
               "type Reader interface {\n\tRead() error\n}\n\n"
               "func New() *Db { return &Db{} }\n\n"
               "func (d *Db) Close() error {\n\treturn nil\n}\n")
        result = extract_file("store/db.go", src)
        k = kinds(result)
        self.assertEqual(k["store/db.go::Db"], "struct")
        self.assertEqual(k["store/db.go::Reader"], "interface")
        self.assertEqual(k["store/db.go::New"], "function")
        self.assertEqual(k["store/db.go::Db.Close"], "method")
        self.assertIn(("store/db.go::Db.Close", "store/db.go::Db"),
                      {(e["source"], e.get("target")) for e in result["edges"]
                       if e["rel"] == "method_of"})

    def test_imports_resolve_to_local_package_by_path_suffix(self):
        self.write("go.mod", "module example.com/app\n")
        self.write("internal/store/db.go", "package store\n")
        self.write("internal/store/tx.go", "package store\n")
        self.write("main.go", 'package main\n\nimport (\n\t"fmt"\n'
                              '\t"example.com/app/internal/store"\n)\n')
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "main.go", "internal/store/",
                                      "imports", "INFERRED"))
        self.assertTrue(self.has_edge(graph, "internal/store/",
                                      "internal/store/db.go", "contains",
                                      "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "main.go", "fmt", "imports",
                                      "EXTRACTED"))

    def test_struct_embedding_is_inheritance(self):
        self.write("a.go", "package a\n\ntype Base struct{}\n\n"
                           "type Child struct {\n\tBase\n\tname string\n}\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "a.go::Child", "a.go::Base",
                                      "inherits", "EXTRACTED"))
        inherits = self.edges(graph, "inherits")
        self.assertEqual(len(inherits), 1)


class TestRust(GraphCase):
    def test_definitions_and_impl_methods(self):
        src = ("pub struct Db { n: u8 }\n"
               "enum Mode { A }\n"
               "pub trait Store { fn get(&self) -> u8; }\n"
               "impl Db {\n    pub fn new() -> Self { Db { n: 0 } }\n}\n"
               "impl Store for Db {\n    fn get(&self) -> u8 { self.n }\n}\n"
               "fn helper<'a>(x: &'a str) -> &'a str { x }\n")
        result = extract_file("src/db.rs", src)
        k = kinds(result)
        self.assertEqual(k["src/db.rs::Db"], "struct")
        self.assertEqual(k["src/db.rs::Mode"], "enum")
        self.assertEqual(k["src/db.rs::Store"], "trait")
        self.assertEqual(k["src/db.rs::Db.new"], "method")
        self.assertEqual(k["src/db.rs::Db.get"], "method")
        self.assertEqual(k["src/db.rs::helper"], "function")
        edges = {(e["source"], e.get("target"), e["rel"])
                 for e in result["edges"]}
        self.assertIn(("src/db.rs::Db", "src/db.rs::Store", "inherits"), edges)

    def test_mod_and_use_resolution(self):
        self.write("src/main.rs", "mod store;\nuse crate::store::Db;\n"
                                  "use std::collections::HashMap;\n")
        self.write("src/store.rs", "pub struct Db;\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(graph, "src/main.rs", "src/store.rs",
                                      "imports", "EXTRACTED"))
        self.assertTrue(self.has_edge(graph, "src/main.rs", "std", "imports"))


class TestJava(GraphCase):
    def test_classes_methods_and_inheritance(self):
        src = ("package com.acme;\n\n"
               "public class Shop extends Base implements Named, Priced {\n"
               "    private int n;\n"
               "    public Shop() { }\n"
               "    public List<String> items(int a) throws IOException {\n"
               "        if (a > 0) { return null; }\n"
               "        return null;\n    }\n}\n"
               "interface Named { String name(); }\n"
               "record Point(int x, int y) {}\n")
        result = extract_file("src/com/acme/Shop.java", src)
        k = kinds(result)
        self.assertEqual(k["src/com/acme/Shop.java::Shop"], "class")
        self.assertEqual(k["src/com/acme/Shop.java::Named"], "interface")
        self.assertEqual(k["src/com/acme/Shop.java::Point"], "record")
        self.assertEqual(k["src/com/acme/Shop.java::Shop.items"], "method")
        self.assertNotIn("src/com/acme/Shop.java::Shop.if", k)
        edges = {(e["source"], e.get("target"), e["rel"])
                 for e in result["edges"]}
        self.assertIn(("src/com/acme/Shop.java::Shop",
                       "src/com/acme/Shop.java::Named", "inherits"), edges)

    def test_import_resolves_by_package_path_suffix(self):
        self.write("src/main/java/com/acme/store/Db.java",
                   "package com.acme.store;\npublic class Db {}\n")
        self.write("src/main/java/com/acme/App.java",
                   "package com.acme;\nimport com.acme.store.Db;\n"
                   "import java.util.List;\npublic class App {}\n")
        graph = build_graph(self.root)
        self.assertTrue(self.has_edge(
            graph, "src/main/java/com/acme/App.java",
            "src/main/java/com/acme/store/Db.java", "imports", "INFERRED"))
        self.assertTrue(self.has_edge(graph,
                                      "src/main/java/com/acme/App.java",
                                      "java.util", "imports", "EXTRACTED"))


if __name__ == "__main__":
    unittest.main()
