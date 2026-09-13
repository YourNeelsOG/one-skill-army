"""Tests for the extractor registry (osa/extractors/__init__.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.extractors import extract_file


class TestRegistry(unittest.TestCase):
    def test_python_file_uses_ast_extractor(self):
        result = extract_file("pkg/mod.py", "def greet():\n    return 1\n")
        self.assertTrue(
            any(n["kind"] == "function" and n["name"] == "greet"
                for n in result["nodes"])
        )

    def test_unknown_extension_yields_only_a_file_node(self):
        result = extract_file("data/blob.xyz", "arbitrary bytes\n")
        self.assertEqual(len(result["nodes"]), 1)
        self.assertEqual(result["nodes"][0]["kind"], "file")
        self.assertEqual(result["nodes"][0]["id"], "data/blob.xyz")

    def test_markdown_headings_become_nodes(self):
        result = extract_file("docs/guide.md", "# Title\n\n## Setup\n")
        headings = [n for n in result["nodes"] if n["kind"] == "heading"]
        self.assertEqual({h["name"] for h in headings}, {"Title", "Setup"})

    def test_markdown_still_emits_a_file_node(self):
        result = extract_file("docs/guide.md", "# Title\n")
        self.assertTrue(any(n["kind"] == "file" for n in result["nodes"]))


if __name__ == "__main__":
    unittest.main()
