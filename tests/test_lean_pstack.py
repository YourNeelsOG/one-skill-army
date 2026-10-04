"""Pin installed pstack routing and policy while reducing entrypoint overhead."""
import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestLeanPstack(unittest.TestCase):
    """Exercise the isolated installed artifacts consumed by an agent."""

    @classmethod
    def setUpClass(cls):
        """Install into temporary storage without touching host skill directories."""
        cls.storage = tempfile.TemporaryDirectory(prefix="osa lean pstack ")
        cls.addClassCleanup(cls.storage.cleanup)
        cls.base = Path(cls.storage.name)
        result = subprocess.run(
            ["bash", str(ROOT / "scripts/install.sh"), "--dir", cls.storage.name],
            capture_output=True, text=True,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def test_every_imported_entrypoint_reaches_one_policy(self):
        """A directly invoked imported skill must resolve the canonical contract."""
        skills = self.base / "skills"
        policy = skills / "poteto-mode/references/runtime.md"
        names = json.loads((skills / "poteto-mode/provenance.json").read_text())["skills"]
        for name in names:
            with self.subTest(skill=name):
                entry = skills / name / "SKILL.md"
                text = entry.read_text()
                self.assertIn("## OSA execution contract", text)
                links = re.findall(r"\]\(([^)]+runtime\.md)\)", text)
                self.assertTrue(links, "Mandatory policy read link is missing")
                self.assertEqual({(entry.parent / link).resolve() for link in links},
                                 {policy.resolve()})
                self.assertFalse("## Skill lookup" in text, "Duplicated skill lookup")
                self.assertFalse("Production edits require a minimal behavioral test" in text,
                                 "Duplicated full policy contract")
        contract = policy.read_text()
        self.assertIn("Production edits require a minimal behavioral test", contract)
        self.assertIn("Never force-push unless the user explicitly requested it", contract)
        self.assertTrue("Resolve another named skill as a sibling" in contract,
                        "Shared skill lookup is missing")

    def test_default_orchestrator_routes_to_poteto(self):
        """Ordinary OSA work must enter the bundled workflow without a mode request."""
        entry = self.base / "skills/one-skill-army/SKILL.md"
        text = entry.read_text()
        self.assertTrue("../poteto-mode/SKILL.md" in text, "Default poteto link is missing")
        # Link destination dots are paths, not sentence boundaries.
        prose = re.sub(r"\]\([^\n)]*\)", "]", text.lower())
        self.assertRegex(prose, r"default[^\n.]*poteto|poteto[^\n.]*default")
        self.assertTrue((entry.parent / "../poteto-mode/SKILL.md").is_file())

    def test_compact_router_preserves_detailed_workflows(self):
        """Keep the full workflow text available without loading it on every task."""
        directory = self.base / "skills/poteto-mode"
        router = directory / "SKILL.md"
        self.assertLessEqual(len(router.read_bytes()), 6000)
        text = router.read_text()
        self.assertIn("references/workflows.md", text)
        self.assertIn("selected", text.lower())
        self.assertIn("playbook", text.lower())
        self.assertIn("principle", text.lower())
        detail = (directory / "references/workflows.md").read_text()
        body = detail.split("## Non-negotiables", 1)[1]
        # Only link destinations can change when moving the retained document.
        normalized = re.sub(r"\]\([^\n)]*\)", "](RESOURCE)", body)
        self.assertEqual(hashlib.sha256(normalized.encode()).hexdigest(),
                         "99254c55749f5627a4a3374961a5643f5e7adb4f887e36ae0fe2a3b2ef018846")


if __name__ == "__main__":
    unittest.main()
