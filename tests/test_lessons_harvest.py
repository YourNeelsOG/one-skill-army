"""Exercise `osa lessons harvest` and `osa lessons due` against sample transcripts.

Every host location is redirected to a temporary directory through the
OSA_* environment overrides, so no test reads real chat history.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)


def stamp(hours_ago):
    return (NOW - timedelta(hours=hours_ago)).isoformat().replace("+00:00", "Z")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


class TestLessonsHarvest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.env = {
            "OSA_CLAUDE_DIR": str(self.base / "claude"),
            "OSA_CODEX_DIR": str(self.base / "codex"),
            "OSA_TRANSCRIPT_DIRS": str(self.base / "other"),
            "OSA_KNOWLEDGE_HOME": str(self.base / "knowledge"),
        }
        patcher = patch.dict(os.environ, self.env)
        patcher.start()
        self.addCleanup(patcher.stop)
        claude_user = {"type": "user", "cwd": "/work/app", "timestamp": stamp(2)}
        write_jsonl(self.base / "claude/-work-app/one.jsonl", [
            dict(claude_user, message={"role": "user", "content": "No, don't use tabs. Always use 2 spaces."}),
            dict(claude_user, message={"role": "user", "content": "No, don't use tabs. Always use 2 spaces."}),
            dict(claude_user, message={"role": "user", "content": "Add a login page"}),
            dict(claude_user, message={"role": "user", "content": [{"type": "tool_result", "content": "TOOL OUTPUT"}]}),
            dict(claude_user, isMeta=True, message={"role": "user", "content": "META TEXT"}),
            dict(claude_user, isSidechain=True, message={"role": "user", "content": "SUBAGENT PROMPT"}),
            dict(claude_user, promptSource="system", message={"role": "user", "content": "SYSTEM NOTICE"}),
            dict(claude_user, message={"role": "user", "content": "<command-name>/model</command-name>"}),
            dict(claude_user, timestamp=stamp(60), message={"role": "user", "content": "Never use var, it is old"}),
            dict(claude_user, message={"role": "user", "content": "my key is sk-ant-abcdefghijklmnopqrstuvwxyz0123456789"}),
        ])
        write_jsonl(self.base / "codex/2026/10/04/rollout-a.jsonl", [
            {"type": "session_meta", "timestamp": stamp(3), "payload": {"cwd": "/work/api"}},
            {"type": "response_item", "timestamp": stamp(3), "payload": {"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": "# AGENTS.md instructions for /work/api\nRULES"},
                {"type": "input_text", "text": "<environment_context><cwd>/work/api</cwd></environment_context>"}]}},
            {"type": "response_item", "timestamp": stamp(3), "payload": {"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": "From now on run pytest with -q"}]}},
            {"type": "response_item", "timestamp": stamp(3), "payload": {"type": "message", "role": "assistant", "content": [
                {"type": "output_text", "text": "ASSISTANT REPLY"}]}},
        ])
        write_jsonl(self.base / "other/grok.jsonl", [
            {"role": "user", "content": "I prefer short commit subjects", "timestamp": stamp(1)},
            {"role": "assistant", "content": "ASSISTANT REPLY"},
        ])

    def lessons(self):
        from osa import lessons
        return lessons

    def test_harvest_keeps_only_recent_user_messages_from_every_host(self):
        entries = self.lessons().harvest(hours=48, now=NOW)
        texts = {entry["text"] for entry in entries}
        self.assertIn("Add a login page", texts)
        self.assertIn("From now on run pytest with -q", texts)
        self.assertIn("I prefer short commit subjects", texts)
        self.assertEqual({entry["host"] for entry in entries}, {"claude", "codex", "other"})
        projects = {entry["text"]: entry["project"] for entry in entries}
        self.assertEqual(projects["From now on run pytest with -q"], "/work/api")
        self.assertEqual(projects["Add a login page"], "/work/app")
        joined = "\n".join(texts)
        for hidden in ("TOOL OUTPUT", "META TEXT", "SUBAGENT PROMPT", "SYSTEM NOTICE", "command-name",
                       "Never use var", "AGENTS.md instructions", "environment_context", "ASSISTANT REPLY"):
            self.assertNotIn(hidden, joined)

    def test_history_copied_into_new_sessions_counts_once(self):
        """Codex and Claude copy earlier turns, ids included, into resumed or forked sessions."""
        copied = {"type": "response_item", "timestamp": stamp(1), "payload": {
            "type": "message", "role": "user", "id": "msg_same",
            "content": [{"type": "input_text", "text": "Keep answers short"}]}}
        for name in ("rollout-b.jsonl", "rollout-c.jsonl"):
            write_jsonl(self.base / "codex/2026/10/04" / name, [copied])
        row = {"type": "user", "cwd": "/work/app", "timestamp": stamp(1), "uuid": "u-same",
               "message": {"role": "user", "content": "Use pnpm here"}}
        write_jsonl(self.base / "claude/-work-app/resumed.jsonl", [row])
        write_jsonl(self.base / "claude/-work-app/forked.jsonl", [row])
        texts = [entry["text"] for entry in self.lessons().harvest(hours=48, now=NOW)]
        self.assertEqual(texts.count("Keep answers short"), 1)
        self.assertEqual(texts.count("Use pnpm here"), 1)

    def test_keeps_answers_the_user_picked_in_question_prompts(self):
        """A choice made through a host question prompt is a decision, often newer than chat text."""
        write_jsonl(self.base / "claude/-work-app/asked.jsonl", [{
            "type": "user", "cwd": "/work/app", "timestamp": stamp(1),
            "message": {"role": "user", "content": [{"type": "tool_result", "content": "TOOL OUTPUT"}]},
            "toolUseResult": {"questions": [], "answers": {"Which default token level?": "ultra (Recommended)"}}}])
        texts = [entry["text"] for entry in self.lessons().harvest(hours=48, now=NOW)]
        self.assertIn('Chose "ultra (Recommended)" for: Which default token level?', texts)
        self.assertNotIn("TOOL OUTPUT", "\n".join(texts))

    def test_drops_interruption_markers_and_bare_menu_picks(self):
        row = {"type": "user", "cwd": "/work/app", "timestamp": stamp(1)}
        write_jsonl(self.base / "claude/-work-app/noise.jsonl", [
            dict(row, message={"role": "user", "content": text})
            for text in ("[Request interrupted by user]", "2", "ok", "1.", "Keep the noise filter")])
        texts = {entry["text"] for entry in self.lessons().harvest(hours=48, now=NOW)}
        self.assertIn("Keep the noise filter", texts)
        for noise in ("[Request interrupted by user]", "2", "ok", "1."):
            self.assertNotIn(noise, texts)

    def unwritable_home(self):
        """Point the user-wide knowledge home at a read-only parent, as in a Codex sandbox."""
        locked = self.base / "locked"
        locked.mkdir()
        locked.chmod(0o555)
        self.addCleanup(locked.chmod, 0o755)
        os.environ["OSA_KNOWLEDGE_HOME"] = str(locked / "knowledge")
        project = self.base / "project"
        project.mkdir()
        return project

    def test_mark_falls_back_to_the_project_when_home_is_read_only(self):
        """Otherwise a sandboxed host stays due forever and harvests after every task."""
        project = self.unwritable_home()
        lessons = self.lessons()
        lessons.mark(now=NOW, project=project)
        self.assertTrue((project / ".osa/knowledge/.last-harvest").is_file())
        self.assertFalse(lessons.due(hours=24, now=NOW + timedelta(hours=1), project=project))

    def test_cli_harvest_survives_a_read_only_home(self):
        project = self.unwritable_home()
        environment = dict(os.environ, PYTHONPATH=str(ROOT))
        result = subprocess.run([sys.executable, "-m", "osa", "lessons", "harvest"], cwd=project,
                                env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("Lessons harvest:", result.stdout)
        due = subprocess.run([sys.executable, "-m", "osa", "lessons", "due"], cwd=project,
                             env=environment, capture_output=True, text=True)
        self.assertEqual(due.returncode, 1, due.stdout)

    def test_cli_harvest_reports_when_no_stamp_can_be_written(self):
        project = self.unwritable_home()
        project.chmod(0o555)
        self.addCleanup(project.chmod, 0o755)
        environment = dict(os.environ, PYTHONPATH=str(ROOT))
        result = subprocess.run([sys.executable, "-m", "osa", "lessons", "harvest"], cwd=project,
                                env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("could not record harvest time", result.stderr)

    def test_render_ranks_corrections_counts_repeats_and_redacts(self):
        lessons = self.lessons()
        text = lessons.render(lessons.harvest(hours=48, now=NOW), budget=4000)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", text)
        self.assertIn("[REDACTED]", text)
        self.assertIn("x2", text)
        self.assertLess(text.index("don't use tabs"), text.index("Add a login page"))
        self.assertLessEqual(len(lessons.render(lessons.harvest(hours=48, now=NOW), budget=300)), 300)

    def test_due_until_marked_then_due_again_after_interval(self):
        lessons = self.lessons()
        self.assertTrue(lessons.due(hours=24, now=NOW))
        lessons.mark(now=NOW)
        self.assertFalse(lessons.due(hours=24, now=NOW + timedelta(hours=23)))
        self.assertTrue(lessons.due(hours=24, now=NOW + timedelta(hours=25)))

    def test_cli_harvest_prints_digest_and_marks(self):
        environment = dict(os.environ, PYTHONPATH=str(ROOT))
        due = subprocess.run([sys.executable, "-m", "osa", "lessons", "due"],
                             env=environment, capture_output=True, text=True)
        self.assertEqual(due.returncode, 0, due.stdout + due.stderr)
        result = subprocess.run([sys.executable, "-m", "osa", "lessons", "harvest", "--hours", "100000"],
                                env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("I prefer short commit subjects", result.stdout)
        self.assertIn("untrusted", result.stdout.lower())
        due = subprocess.run([sys.executable, "-m", "osa", "lessons", "due"],
                             env=environment, capture_output=True, text=True)
        self.assertEqual(due.returncode, 1, due.stdout)

    def test_session_start_hook_announces_a_due_harvest(self):
        environment = {k: v for k, v in os.environ.items()
                       if k not in ("OSA_DEFAULT_MODE", "CLAUDE_PLUGIN_ROOT", "CURSOR_PLUGIN_ROOT")}
        with tempfile.TemporaryDirectory() as project:
            result = subprocess.run(["bash", str(ROOT / "hooks/session-start")], cwd=project,
                                    env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("update-lesson", json.dumps(json.loads(result.stdout)))

    def test_update_lesson_skill_and_command_run_the_harvest(self):
        for path in ("skills/update-lesson/SKILL.md", "commands/update-lesson.md"):
            self.assertIn("lessons harvest", (ROOT / path).read_text(), path)


if __name__ == "__main__":
    unittest.main()
