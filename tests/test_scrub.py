"""Tests for the comment and string scrubber (osa/extractors/scrub.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.extractors.scrub import scrub

C_LIKE = {"line": ["//"], "block": [("/*", "*/")], "strings": ['"', "'", "`"]}


class TestScrub(unittest.TestCase):
    def test_length_and_newlines_are_preserved(self):
        src = 'a = "x // y"; /* multi\nline */ b // tail\nc'
        out = scrub(src, **C_LIKE)
        self.assertEqual(len(out), len(src))
        self.assertEqual(out.count("\n"), src.count("\n"))
        self.assertEqual([i for i, ch in enumerate(out) if ch == "\n"],
                         [i for i, ch in enumerate(src) if ch == "\n"])

    def test_line_comment_is_blanked(self):
        out = scrub('import x from "a" // import y from "b"\n', **C_LIKE)
        self.assertIn('import x from "', out)
        self.assertNotIn("import y", out)

    def test_block_comment_is_blanked(self):
        out = scrub("/* import z */ code", **C_LIKE)
        self.assertNotIn("import", out)
        self.assertTrue(out.endswith("code"))

    def test_string_contents_blanked_but_quotes_kept(self):
        src = 'x = "// not a comment"; y'
        out = scrub(src, **C_LIKE)
        self.assertEqual(out, 'x = "' + " " * len("// not a comment") + '"; y')

    def test_escaped_quote_does_not_end_string(self):
        src = 'a = "he said \\"hi\\"" + b'
        out = scrub(src, **C_LIKE)
        self.assertTrue(out.endswith('" + b'))
        self.assertEqual(out.count('"'), 2)

    def test_comment_marker_inside_string_is_ignored(self):
        out = scrub("s = '/* no */'; real()", **C_LIKE)
        self.assertIn("real()", out)

    def test_hash_comment_needs_word_start(self):
        spec = {"line": ["#"], "block": [], "strings": ['"', "'"]}
        out = scrub("echo $# items # trailing note\n", **spec)
        self.assertIn("$#", out)
        self.assertNotIn("trailing", out)

    def test_sql_comments(self):
        spec = {"line": ["--"], "block": [("/*", "*/")], "strings": ["'"]}
        out = scrub("CREATE TABLE t (id int); -- REFERENCES ghost\n", **spec)
        self.assertNotIn("ghost", out)
        self.assertIn("CREATE TABLE t", out)

    def test_unterminated_string_stops_at_end_of_input(self):
        out = scrub('x = "open', **C_LIKE)
        self.assertEqual(len(out), len('x = "open'))


if __name__ == "__main__":
    unittest.main()
