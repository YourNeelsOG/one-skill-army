"""Tests for the Python AST extractor (osa/extractors/python_ast.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.extractors.python_ast import extract


class TestPythonExtractor(unittest.TestCase):
    def test_extracts_function_definition_as_symbol_node(self):
        result = extract("pkg/mod.py", "def greet():\n    return 1\n")
        symbols = [n for n in result["nodes"] if n["kind"] == "function"]
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0]["name"], "greet")
        self.assertEqual(symbols[0]["path"], "pkg/mod.py")
        self.assertEqual(symbols[0]["lang"], "python")

    def test_emits_a_file_node_for_the_source(self):
        result = extract("pkg/mod.py", "x = 1\n")
        files = [n for n in result["nodes"] if n["kind"] == "file"]
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["id"], "pkg/mod.py")
        self.assertEqual(files[0]["path"], "pkg/mod.py")

    def test_extracts_class_definition_as_symbol_node(self):
        result = extract("pkg/mod.py", "class Widget:\n    pass\n")
        classes = [n for n in result["nodes"] if n["kind"] == "class"]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]["name"], "Widget")

    def test_emits_defines_edge_from_file_to_each_symbol(self):
        result = extract("pkg/mod.py", "def greet():\n    return 1\n")
        defines = [e for e in result["edges"] if e["rel"] == "defines"]
        self.assertIn(
            {"source": "pkg/mod.py", "target": "pkg/mod.py::greet",
             "rel": "defines", "confidence": "EXTRACTED"},
            defines,
        )

    def test_import_is_a_pending_edge_with_external_fallback(self):
        # One file cannot tell a local module from an external package, so
        # the import is left for osa/resolve.py with both options listed.
        result = extract("pkg/mod.py", "import os\n")
        imports = [e for e in result["edges"] if e["rel"] == "imports"]
        self.assertEqual(imports[0]["resolve"]["files"],
                         ["os.py", "os/__init__.py"])
        self.assertEqual(imports[0]["resolve"]["module"], "os")

    def test_extracts_from_import_module(self):
        result = extract("pkg/mod.py", "from collections import OrderedDict\n")
        imports = [e for e in result["edges"] if e["rel"] == "imports"]
        self.assertTrue(any(e["resolve"]["module"] == "collections"
                            for e in imports))

    def test_async_function_counts_as_function_symbol(self):
        result = extract("pkg/mod.py", "async def fetch():\n    return 1\n")
        symbols = [n for n in result["nodes"] if n["kind"] == "function"]
        self.assertEqual([s["name"] for s in symbols], ["fetch"])

    def test_extracts_calls_edge_between_local_functions(self):
        src = "def a():\n    b()\n\ndef b():\n    return 1\n"
        result = extract("pkg/mod.py", src)
        calls = [e for e in result["edges"] if e["rel"] == "calls"]
        self.assertIn(
            {"source": "pkg/mod.py::a", "target": "pkg/mod.py::b",
             "rel": "calls", "confidence": "EXTRACTED", "line": 2},
            calls,
        )

    def test_no_calls_edge_to_undefined_name(self):
        # Calls to names not defined in this file are never final edges; at
        # most they are pending, and the resolver drops them unless unique.
        result = extract("pkg/mod.py", "def a():\n    external_thing()\n")
        calls = [e for e in result["edges"]
                 if e["rel"] == "calls" and "target" in e]
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
