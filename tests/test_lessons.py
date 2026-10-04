"""Check that every entry point tells agents to read and update lessons.md.

Lessons are instruction-driven: no engine code writes them. These tests pin
the instructions at each place a host reads them, so a host never starts a
session without the user-wide and project lessons in scope.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

USER_FILE = "~/.osa/knowledge/lessons.md"
PROJECT_FILE = ".osa/knowledge/lessons.md"


class TestLessons(unittest.TestCase):
    def assert_both_scopes(self, text, where):
        self.assertIn(USER_FILE, text, where)
        self.assertIn(PROJECT_FILE, text, where)

    def test_memory_skill_defines_lessons_contract(self):
        text = (ROOT / "skills/memory/SKILL.md").read_text()
        self.assertIn("## Lessons", text)
        self.assert_both_scopes(text, "memory skill")
        # The section's example block has its own "## " headings, so stop at the
        # next real section instead of the next heading.
        section = text.split("## Lessons", 1)[1].split("## Compaction protocol", 1)[0].lower()
        for phrase in ("seen", "never grant", "150 lines"):
            self.assertIn(phrase, section)

    def test_orchestrator_and_project_rules_read_lessons(self):
        for name in ("skills/one-skill-army/SKILL.md", "AGENTS.md"):
            text = (ROOT / name).read_text()
            self.assert_both_scopes(text, name)
            self.assertIn("update-lesson", text, name)

    def test_project_install_anchor_reads_lessons(self):
        from osa.install import install_project
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            install_project(project, ROOT, hosts=("codex",))
            anchor = (project / "AGENTS.md").read_text()
            self.assert_both_scopes(anchor, "anchor")
            # Hosts without a session hook rely on the anchor for automatic harvests.
            self.assertIn("lessons due", anchor)
            self.assertIn("update-lesson", anchor)

    def test_session_start_hook_reads_lessons(self):
        environment = {k: v for k, v in os.environ.items()
                       if k not in ("OSA_DEFAULT_MODE", "CLAUDE_PLUGIN_ROOT", "CURSOR_PLUGIN_ROOT")}
        with tempfile.TemporaryDirectory() as project:
            result = subprocess.run(["bash", str(ROOT / "hooks/session-start")], cwd=project,
                                    env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.dumps(json.loads(result.stdout))
        self.assert_both_scopes(payload.split("Session start protocol", 1)[1], "hook protocol")


if __name__ == "__main__":
    unittest.main()
