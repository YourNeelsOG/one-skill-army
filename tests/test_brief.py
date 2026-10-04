"""Tests for the harness brief (osa/brief.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.brief import brief


class TestBrief(unittest.TestCase):
    def test_brief_routes_to_default_poteto_workflow_on_demand(self):
        """Host reminders activate the workflow without loading every playbook."""
        text = brief().lower()
        self.assertIn("poteto-mode", text)
        self.assertIn("default workflow", text)
        self.assertIn("selected playbook", text)

    def test_brief_names_the_core_rails(self):
        text = brief().lower()
        for keyword in ("git-safety", "verification", "minimal", "hallucinat"):
            self.assertIn(keyword, text)

    def test_brief_states_the_overhead_compression_rule(self):
        text = brief().lower()
        self.assertIn("overhead", text)
        # the invariant: never compress the actual output
        self.assertIn("never", text)
        self.assertIn("output", text)

    def test_brief_points_to_the_prebuilt_context(self):
        self.assertIn(".osa/context.md", brief())

    def test_brief_persists_across_model_switch(self):
        self.assertIn("model switch", brief().lower())

    def test_levels_change_the_directive(self):
        self.assertNotEqual(brief(level="lite"), brief(level="ultra"))

    def test_default_level_is_ultra_everywhere(self):
        """Every host entry point must agree on the shipped default level."""
        import json, os, subprocess, tempfile
        from osa.hook import prompt, session_start
        self.assertEqual(brief(), brief(level="ultra"))
        self.assertEqual(prompt(), brief(level="ultra"))
        root = Path(__file__).resolve().parent.parent
        environment = {k: v for k, v in os.environ.items()
                       if k not in ("OSA_DEFAULT_MODE", "CLAUDE_PLUGIN_ROOT", "CURSOR_PLUGIN_ROOT")}
        with tempfile.TemporaryDirectory() as project:
            result = subprocess.run(["bash", str(root / "hooks/prompt-reminder")], cwd=project,
                                    env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("level: ultra", json.dumps(json.loads(result.stdout)))


if __name__ == "__main__":
    unittest.main()
