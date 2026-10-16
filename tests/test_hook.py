"""Tests for the harness hook entry (osa/hook.py + CLI 'hook')."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.hook import session_start, prompt
from osa.cli import main


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = main(argv)
    return code, buf.getvalue()


class TestHook(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "cli.py").write_text("def run():\n    return 1\n")

    def tearDown(self):
        self._tmp.cleanup()

    def test_session_start_indexes_when_missing(self):
        text = session_start(self.root)
        self.assertTrue((self.root / ".osa" / "graph.json").is_file())
        self.assertIn("ONE SKILL ARMY ACTIVE", text)

    def test_session_start_mentions_context_when_available(self):
        text = session_start(self.root)
        self.assertIn(".osa/context.md", text)

    def test_prompt_returns_the_brief(self):
        self.assertIn("ONE SKILL ARMY ACTIVE", prompt())

    def write_index(self):
        "A project knowledge index with a hot list and two route rows."
        knowledge = self.root / ".osa" / "knowledge"
        (knowledge / "topics").mkdir(parents=True)
        (knowledge / "topics" / "cart.md").write_text("Cart totals include tax.\n")
        (knowledge / "index.md").write_text(
            "# Lessons index\n\n## Hot list\n\n1. Change only what was asked.\n"
            "2. Run tests before claiming done.\n\n## Routes\n\n"
            "| Keywords | Files |\n|---|---|\n"
            "| cart, checkout | topics/cart.md |\n| auth | topics/auth.md |\n")

    def test_prompt_injects_hot_list_and_matched_routes(self):
        self.write_index()
        text = prompt(self.root, user_prompt="fix the cart total")
        self.assertIn("Change only what was asked", text)
        self.assertIn(".osa/knowledge/topics/cart.md", text)
        self.assertNotIn("topics/auth.md", text)

    def test_prompt_without_index_keeps_brief_only(self):
        self.assertNotIn("Hot list", prompt(self.root, user_prompt="fix the cart"))

    def test_prompt_lists_hot_list_without_routes_when_no_match(self):
        self.write_index()
        text = prompt(self.root, user_prompt="update the readme")
        self.assertIn("Change only what was asked", text)
        self.assertNotIn("topics/cart.md", text)

    def test_cli_hook_prompt_reads_stdin_payload(self):
        self.write_index()
        payload = io.StringIO(json.dumps({"prompt": "fix the cart total"}))
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), patch("sys.stdin", payload):
            code = main(["hook", "prompt", "--path", str(self.root), "--stdin"])
        self.assertEqual(code, 0)
        self.assertIn("topics/cart.md", buffer.getvalue())

    def test_cli_hook_session_start(self):
        code, out = run(["hook", "session-start", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("ONE SKILL ARMY ACTIVE", out)

    def test_cli_hook_prompt(self):
        code, out = run(["hook", "prompt", "--path", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("ONE SKILL ARMY ACTIVE", out)


if __name__ == "__main__":
    unittest.main()
