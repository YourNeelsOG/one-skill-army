"""Tests for the harness brief (osa/brief.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osa.brief import brief


class TestBrief(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
