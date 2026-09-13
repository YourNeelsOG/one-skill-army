"""Tests for the harness hook entry (osa/hook.py + CLI 'hook')."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

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
