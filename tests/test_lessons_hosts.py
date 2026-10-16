"""Exercise the native host readers and digest sections of the lessons engine.

Each host store is built as a fixture under a temporary directory and reached
only through its OSA_* environment override, so no test reads real chat
history. Timestamps are pinned to a fixed NOW so window filters are provable.
"""
import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)


def at(hours_ago):
    "A UTC datetime `hours_ago` hours before the fixed NOW."
    return NOW - timedelta(hours=hours_ago)


def ms(when):
    "Epoch milliseconds, the unit both SQLite chat stores use."
    return int(when.timestamp() * 1000)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def connect(path):
    "Create a fixture SQLite file and return a writable connection."
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(path))


PART_SCHEMA = (
    "create table message (id text primary key, session_id text, time_created integer, data text);"
    "create table part (id text, message_id text, session_id text, time_created integer, data text);"
    "create table session (id text, directory text);")


class HostFixture(unittest.TestCase):
    """Temp stores and env overrides; each test fills only the hosts it needs."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.env = {
            "OSA_CLAUDE_DIR": str(self.base / "claude"),
            "OSA_CODEX_DIR": str(self.base / "codex"),
            "OSA_TRANSCRIPT_DIRS": "",
            "OSA_KNOWLEDGE_HOME": str(self.base / "knowledge"),
            "OSA_ZCODE_DB": str(self.base / "zcode" / "db.sqlite"),
            "OSA_OPENCODE_DB": str(self.base / "opencode" / "opencode.db"),
            "OSA_T3_DIR": str(self.base / "t3"),
            "OSA_GROK_DIR": str(self.base / "grok"),
            "OSA_CURSOR_DIR": str(self.base / "cursor"),
        }
        patcher = patch.dict(os.environ, self.env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def collect(self, **kwargs):
        from osa import lessons
        return lessons.collect(now=NOW, **kwargs)

    def zcode_fixture(self):
        "ZCode CLI store: failing pytest runs, an edit, and secrets in text and output."
        con = connect(self.base / "zcode" / "db.sqlite")
        con.executescript(PART_SCHEMA)
        con.execute("insert into session values ('sess-1', '/work/lms')")
        for mid, role in (("m1", "user"), ("m2", "assistant"), ("m3", "user")):
            con.execute("insert into message values (?, 'sess-1', ?, ?)",
                        (mid, ms(at(1)), json.dumps({"role": role})))
        parts = (
            ("p1", "m1", {"type": "text", "text": "never use tabs in this repo"}),
            ("p2", "m2", {"type": "text", "text": "assistant answers are not harvested"}),
            ("p3", "m2", {"type": "tool", "tool": "Bash", "state": {"status": "completed",
                          "input": {"command": "pytest tests -q"}, "output": "exit code 1\nFAILED two tests"}}),
            ("p4", "m2", {"type": "tool", "tool": "Bash", "state": {"status": "completed",
                          "input": {"command": "pytest tests -q"}, "output": "exit code 1\nFAILED again"}}),
            ("p5", "m2", {"type": "tool", "tool": "Edit", "state": {"status": "completed",
                          "input": {"file_path": "src/app.py"}}}),
            ("p6", "m3", {"type": "text", "text": "deploy token=supersecret123 please"}),
            ("p7", "m2", {"type": "tool", "tool": "Bash", "state": {"status": "completed",
                          "input": {"command": "deploy token=supersecret123"},
                          "output": "error: token=supersecret123 rejected"}}),
        )
        for pid, mid, data in parts:
            con.execute("insert into part values (?, ?, 'sess-1', ?, ?)",
                        (pid, mid, ms(at(1)), json.dumps(data)))
        # A second session with the same failing first try, so cross-chat
        # mistake detection has two chats to compare.
        con.execute("insert into session values ('sess-1b', '/work/lms')")
        con.execute("insert into message values ('m4', 'sess-1b', ?, ?)",
                    (ms(at(1)), json.dumps({"role": "assistant"})))
        con.execute("insert into part values ('p8', 'm4', 'sess-1b', ?, ?)",
                    (ms(at(1)), json.dumps({"type": "tool", "tool": "Bash", "state": {
                        "status": "completed", "input": {"command": "pytest tests -q"},
                        "output": "exit code 1\nFAILED in chat two"}})))
        con.commit()
        con.close()

    def opencode_fixture(self):
        "opencode store: same shape as ZCode, project read from the session table."
        con = connect(self.base / "opencode" / "opencode.db")
        con.executescript(PART_SCHEMA)
        con.execute("insert into session values ('sess-2', '/work/site')")
        for mid, role in (("m1", "user"), ("m2", "assistant")):
            con.execute("insert into message values (?, 'sess-2', ?, ?)",
                        (mid, ms(at(2)), json.dumps({"role": role})))
        parts = (
            ("p1", "m1", {"type": "text", "text": "always run the formatter before committing"}),
            ("p2", "m2", {"type": "tool", "tool": "bash", "state": {"status": "completed",
                          "input": {"command": "npm test"}, "output": "exit code 1\n2 failed"}}),
            ("p3", "m2", {"type": "tool", "tool": "write", "state": {"status": "completed",
                          "input": {"file_path": "src/header.tsx"}}}),
        )
        for pid, mid, data in parts:
            con.execute("insert into part values (?, ?, 'sess-2', ?, ?)",
                        (pid, mid, ms(at(2)), json.dumps(data)))
        con.commit()
        con.close()

    def grok_fixture(self):
        "Grok CLI session: prompt with prompt_index, one tool call and its result."
        write_jsonl(self.base / "grok" / "sessions" / "aa" / "sess-3" / "chat_history.jsonl", (
            {"type": "user", "prompt_index": 0,
             "content": [{"type": "text", "text": "stop adding spinners everywhere"}]},
            {"type": "assistant", "tool_calls": [{"id": "c1", "name": "bash",
                                                  "arguments": json.dumps({"command": "npm run build"})}]},
            {"type": "tool_result", "tool_call_id": "c1", "content": "error: build failed"},
        ))

    def cursor_fixture(self):
        "Cursor CLI prompt history: plain strings and object entries."
        path = self.base / "cursor" / "chats" / "aa" / "bb" / "prompt_history.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(["make the header sticky again", {"text": "keep the answers short"}]))

    def t3_fixture(self):
        "T3 Code store: one user message and one failed command activity."
        con = connect(self.base / "t3" / "state.sqlite")
        con.executescript(
            "create table projection_thread_sessions (thread_id text, provider_name text);"
            "create table projection_thread_messages (message_id text, thread_id text,"
            " created_at text, role text, text text);"
            "create table projection_thread_activities (activity_id text, thread_id text,"
            " created_at text, kind text, payload_json text);")
        con.execute("insert into projection_thread_sessions values ('t1', 'grok')")
        con.execute("insert into projection_thread_messages values ('tm1', 't1', ?, 'user', ?)",
                    (at(2).isoformat(), "don't auto-commit anything"))
        payload = {"status": "completed", "itemType": "command_execution",
                   "data": {"command": "git push origin dev",
                            "rawOutput": {"exitCode": 1, "stderr": "rejected"}}}
        con.execute("insert into projection_thread_activities values ('a1', 't1', ?, 'tool.completed', ?)",
                    (at(1).isoformat(), json.dumps(payload)))
        con.commit()
        con.close()


class TestNativeReaders(HostFixture):
    def test_collect_with_no_stores_returns_empty(self):
        self.assertEqual(self.collect(hours=48), [])

    def test_zcode_yields_users_commands_and_edits(self):
        self.zcode_fixture()
        events = self.collect(hours=48)
        users = [e for e in events if e["kind"] == "user"]
        self.assertEqual([u["text"] for u in users],
                         ["never use tabs in this repo", "deploy token=[REDACTED] please"])
        self.assertEqual(users[0]["host"], "zcode")
        self.assertEqual(users[0]["project"], "/work/lms")
        cmds = [e for e in events if e["kind"] == "cmd"]
        self.assertEqual(cmds[0]["cmd"], "pytest tests -q")
        self.assertTrue(cmds[0]["err"])
        self.assertEqual([e["file"] for e in events if e["kind"] == "edit"], ["src/app.py"])

    def test_zcode_scrubs_secrets_in_commands_and_output(self):
        self.zcode_fixture()
        events = self.collect(hours=48)
        deploy = next(e for e in events if e["kind"] == "cmd" and e["cmd"].startswith("deploy"))
        self.assertNotIn("supersecret123", deploy["cmd"] + deploy["out"])
        self.assertIn("[REDACTED]", deploy["cmd"])

    def test_opencode_yields_users_and_failures(self):
        self.opencode_fixture()
        events = self.collect(hours=48)
        users = [e for e in events if e["kind"] == "user"]
        self.assertEqual([u["text"] for u in users], ["always run the formatter before committing"])
        self.assertEqual(users[0]["project"], "/work/site")
        cmd = next(e for e in events if e["kind"] == "cmd")
        self.assertEqual(cmd["cmd"], "npm test")
        self.assertTrue(cmd["err"])
        self.assertEqual(cmd["host"], "opencode")

    def test_grok_yields_prompt_and_failed_command(self):
        self.grok_fixture()
        events = self.collect(hours=48)
        self.assertEqual([e["text"] for e in events if e["kind"] == "user"],
                         ["stop adding spinners everywhere"])
        cmd = next(e for e in events if e["kind"] == "cmd")
        self.assertEqual(cmd["cmd"], "npm run build")
        self.assertTrue(cmd["err"])
        self.assertEqual(cmd["sid"], "sess-3")

    def test_cursor_yields_prompt_history(self):
        self.cursor_fixture()
        events = self.collect(hours=48)
        self.assertEqual([e["text"] for e in events if e["kind"] == "user"],
                         ["make the header sticky again", "keep the answers short"])
        self.assertTrue(all(e["host"] == "cursor" for e in events))

    def test_t3_yields_message_and_failed_push(self):
        self.t3_fixture()
        events = self.collect(hours=48)
        users = [e for e in events if e["kind"] == "user"]
        self.assertEqual(users[0]["text"], "don't auto-commit anything")
        self.assertEqual(users[0]["host"], "t3-grok")
        cmd = next(e for e in events if e["kind"] == "cmd")
        self.assertEqual(cmd["cmd"], "git push origin dev")
        self.assertTrue(cmd["err"])

    def test_harvest_still_returns_plain_user_entries(self):
        self.zcode_fixture()
        from osa import lessons
        entries = lessons.harvest(hours=48, now=NOW)
        self.assertEqual(set(entries[0]), {"host", "project", "time", "text"})
        self.assertEqual(len(entries), 2)

    def test_cli_harvest_prints_new_sections(self):
        self.zcode_fixture()
        environment = dict(os.environ, PYTHONPATH=str(ROOT))
        result = subprocess_run(["lessons", "harvest", "--hours", "100000"], environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("never use tabs in this repo", result.stdout)
        self.assertIn("## Tool mistakes across chats", result.stdout)
        self.assertIn("first try failed in 2 chats", result.stdout)
        self.assertIn("`pytest tests`", result.stdout)
        self.assertNotIn("assistant answers are not harvested", result.stdout)
        self.assertNotIn("supersecret123", result.stdout)


def subprocess_run(arguments, environment):
    "Run the engine through python -m osa with the fixture environment."
    import subprocess
    return subprocess.run([sys.executable, "-m", "osa"] + arguments,
                          env=environment, capture_output=True, text=True)


class TestDigestSections(unittest.TestCase):
    "The render sections built from cmd and edit events."

    def event(self, kind, sid="s1", hours=1, **fields):
        event = {"host": "claude", "sid": sid, "project": "/w", "time": at(hours), "kind": kind}
        event.update(fields)
        return event

    def test_render_reports_tool_mistakes_and_blame(self):
        from osa import lessons
        events = [
            self.event("edit", hours=5, file="src/cart.ts"),
            self.event("user", hours=4.9, text="no, the cart total is still wrong"),
            self.event("edit", hours=4, file="src/cart.ts"),
            self.event("user", hours=3.9, text="still wrong, revert it"),
            self.event("cmd", hours=2, cmd="pytest tests", err=True, out="1 failed"),
            self.event("cmd", sid="s2", hours=2, cmd="pytest tests", err=True, out="2 failed: boom"),
            self.event("cmd", sid="s3", hours=2, cmd="pytest tests", err=False, out="all good"),
            self.event("cmd", sid="s3", hours=1.9, cmd="pytest tests", err=True, out="1 failed"),
            self.event("cmd", sid="s4", hours=2, cmd="npm test", err=True, out="error: boom"),
            self.event("cmd", sid="s4", hours=1.9, cmd="npm test", err=True, out="error: boom"),
            self.event("cmd", hours=2, cmd="git status", err=False, out="clean"),
        ]
        text = lessons.render(lessons.users(events), budget=8000, events=events)
        self.assertIn("commands (", text)
        self.assertIn("## Tool mistakes across chats", text)
        self.assertIn("first try failed in 2 chats, 3 failures total", text)
        self.assertIn("`pytest tests`", text)
        # npm test failed twice, but only inside one chat: not a cross-chat habit.
        self.assertNotIn("`npm test`", text)
        self.assertNotIn("`git status`", text)
        self.assertNotIn("## Commands that failed 2+ times", text)
        self.assertIn("## Files edited right before a correction", text)
        self.assertIn("2 corrections", text)
        self.assertIn("`src/cart.ts`", text)

    def test_render_respects_budget_across_sections(self):
        from osa import lessons
        events = []
        for index in range(40):
            for suffix in ("a", "b"):
                for _ in range(2):
                    events.append(self.event("cmd", sid=f"s{index}{suffix}", hours=1,
                                             cmd=f"make thing{index}", err=True, out="error: boom"))
        text = lessons.render([], budget=400, events=events)
        self.assertLessEqual(len(text), 400)

    def test_render_without_events_matches_old_output(self):
        from osa import lessons
        entries = [{"host": "claude", "project": "/w", "time": at(1), "text": "always use 2 spaces"}]
        text = lessons.render(entries, budget=4000)
        self.assertIn("always use 2 spaces", text)
        self.assertNotIn("## Commands", text)
        self.assertNotIn("## Tool mistakes", text)


class TestKnowledgeSeed(unittest.TestCase):
    def test_ensure_user_knowledge_seeds_once(self):
        from osa import lessons
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(os.environ, {"OSA_KNOWLEDGE_HOME": temporary}):
                path = lessons.ensure_user_knowledge()
                self.assertTrue(Path(path).is_file())
                self.assertIn("# Lessons", Path(path).read_text())
                mistakes = Path(temporary) / "mistakes.md"
                self.assertTrue(mistakes.is_file())
                self.assertIn("Tool mistakes", mistakes.read_text())
                Path(path).write_text("# custom\n")
                mistakes.write_text("# custom mistakes\n")
                lessons.ensure_user_knowledge()
                self.assertEqual(Path(path).read_text(), "# custom\n")
                self.assertEqual(mistakes.read_text(), "# custom mistakes\n")

    def test_cli_install_seeds_user_knowledge(self):
        "A fresh `osa install` leaves the user-wide lessons and mistakes seeds."
        from types import SimpleNamespace
        from osa import cli
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "app"
            project.mkdir()
            knowledge = Path(temporary) / "knowledge"
            with patch.dict(os.environ, {"OSA_KNOWLEDGE_HOME": str(knowledge)}):
                code = cli._cmd_install(SimpleNamespace(path=str(project), hosts=("codex",), level="ultra"))
            self.assertEqual(code, 0)
            self.assertTrue((knowledge / "lessons.md").is_file())
            self.assertTrue((knowledge / "mistakes.md").is_file())


if __name__ == "__main__":
    unittest.main()
