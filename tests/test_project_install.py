"""Exercise project installation through its public API in disposable directories."""
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestProjectInstall(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="osa project ")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "consumer project"
        self.project.mkdir()
        self.source = self.base / "package source"
        for name in ("one-skill-army", "poteto-mode"):
            directory = self.source / "skills" / name
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text("# " + name + "\n")
        (self.source / "commands").mkdir()
        (self.source / "commands/poteto-mode.md").write_text("Use poteto\n")
        (self.source / "commands/army.md").write_text("Set level\n")
        (self.source / "hooks").mkdir()
        (self.source / "hooks/session-start").write_text("#!/bin/sh\nexit 0\n")

    def installer(self):
        try:
            return importlib.import_module("osa.install")
        except ModuleNotFoundError:
            self.fail("Project installation API is unavailable")

    def test_installs_project_payload_and_preserves_existing_content(self):
        (self.project / "AGENTS.md").write_text("User rules\n")
        (self.project / "CLAUDE.md").write_text("Claude rules\n")
        (self.project / ".osa").mkdir()
        config = {"defaultMode": "lite", "custom": {"keep": True}}
        (self.project / ".osa/config.json").write_text(json.dumps(config))
        memory = self.project / ".osa/memory"
        memory.mkdir()
        (memory / "MEMORY.md").write_text("Keep memory\n")
        custom_skill = self.project / ".claude/skills/custom"
        custom_skill.mkdir(parents=True)
        (custom_skill / "SKILL.md").write_text("Custom\n")
        api = self.installer()
        receipt = api.install_project(self.project, self.source)
        self.assertEqual(receipt["level"], "lite")
        self.assertEqual(receipt["skill_count"], 2)
        self.assertEqual(receipt["command_count"], 2)
        self.assertEqual(receipt["hosts"], ["codex", "claude", "grok", "zcode"])
        for host in ("agents", "claude", "grok", "zcode"):
            link = self.project / ("." + host) / "skills/poteto-mode"
            self.assertTrue(link.is_symlink())
            self.assertEqual((link / "SKILL.md").read_text(), "# poteto-mode\n")
        for anchor, original in (("AGENTS.md", "User rules\n"), ("CLAUDE.md", "Claude rules\n")):
            text = (self.project / anchor).read_text()
            self.assertTrue(text.startswith(original))
            self.assertIn(".osa/pack/skills/poteto-mode/SKILL.md", text)
            self.assertIn("automatically", text)
        anchors = [(self.project / name).read_text() for name in ("AGENTS.md", "CLAUDE.md")]
        self.assertEqual(api.install_project(self.project, self.source), receipt)
        self.assertEqual(anchors, [(self.project / name).read_text() for name in ("AGENTS.md", "CLAUDE.md")])
        self.assertEqual(json.loads((self.project / ".osa/config.json").read_text()), config)
        self.assertEqual((memory / "MEMORY.md").read_text(), "Keep memory\n")
        self.assertEqual((custom_skill / "SKILL.md").read_text(), "Custom\n")
        self.assertTrue(api.doctor_project(self.project)["ok"])
        (self.project / ".osa/pack/skills/poteto-mode/SKILL.md").unlink()
        self.assertFalse(api.doctor_project(self.project)["ok"])

    def test_default_level_is_ultra(self):
        receipt = self.installer().install_project(self.project, self.source)
        self.assertEqual(receipt["level"], "ultra")
        self.assertIn("installed default `ultra`", (self.project / "AGENTS.md").read_text())

    def test_skill_wrapper_commands_link_only_where_skills_lack_slash_entries(self):
        """Claude and Grok list skills as slash entries, so a same-name wrapper duplicates it."""
        self.installer().install_project(self.project, self.source)
        for host in ("claude", "grok"):
            commands = self.project / ("." + host) / "commands"
            self.assertTrue((commands / "army.md").is_symlink())
            self.assertFalse(commands.joinpath("poteto-mode.md").exists())
        for name in ("army.md", "poteto-mode.md"):
            self.assertTrue((self.project / ".zcode/commands" / name).is_symlink())

    def test_refuses_an_osa_source_checkout_without_mutation(self):
        """npx runs from the npm cache, so the overlap check alone misses the source repo."""
        (self.project / "osa").mkdir()
        (self.project / "osa/install.py").write_text("# engine\n")
        (self.project / "skills/one-skill-army").mkdir(parents=True)
        (self.project / "skills/one-skill-army/SKILL.md").write_text("# orchestrator\n")
        before = sorted(path.relative_to(self.project) for path in self.project.rglob("*"))
        with self.assertRaisesRegex(ValueError, "source checkout"):
            self.installer().install_project(self.project, self.source)
        self.assertEqual(sorted(path.relative_to(self.project) for path in self.project.rglob("*")), before)

    def test_rejects_unsafe_inputs_without_mutation(self):
        api = self.installer()
        for kwargs in ({"hosts": ("unknown",)}, {"level": "maximum"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                api.install_project(self.project, self.source, **kwargs)
            self.assertEqual(list(self.project.iterdir()), [])
        with self.assertRaises(ValueError):
            api.install_project(self.source, self.source)
        self.assertFalse((self.source / ".osa").exists())

    def test_refuses_collisions_and_malformed_config_before_copying(self):
        api = self.installer()
        scenarios = ((".osa/config.json", "[1]"), (".osa/config.json", "broken"),
                     (".osa/pack/user.txt", "owned by user"),
                     (".agents/skills/poteto-mode/user.txt", "user skill"),
                     ("AGENTS.md", "<!-- OSA:BEGIN -->\nbroken marker\n"))
        for index, (relative, content) in enumerate(scenarios):
            project = self.base / ("collision " + str(index))
            target = project / relative
            target.parent.mkdir(parents=True)
            target.write_text(content)
            before = sorted(str(path.relative_to(project)) for path in project.rglob("*"))
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                api.install_project(project, self.source)
            self.assertEqual(target.read_text(), content)
            self.assertEqual(sorted(str(path.relative_to(project)) for path in project.rglob("*")), before)

    def test_explicit_level_updates_only_owned_config_key(self):
        api = self.installer()
        (self.project / ".osa").mkdir()
        (self.project / ".osa/config.json").write_text('{"custom": 7}')
        result = api.install_project(self.project, self.source, hosts=("codex",), level="ultra")
        self.assertEqual(result["level"], "ultra")
        self.assertEqual(json.loads((self.project / ".osa/config.json").read_text()),
                         {"custom": 7, "defaultMode": "ultra"})

    def test_empty_resource_directories_remain_owned(self):
        api = self.installer()
        (self.source / "skills/poteto-mode/empty").mkdir()
        api.install_project(self.project, self.source)
        self.assertTrue(api.doctor_project(self.project)["ok"])
        api.install_project(self.project, self.source)

    def test_refuses_symlinked_discovery_parent_and_source_resource(self):
        api = self.installer()
        outside = self.base / "outside"
        outside.mkdir()
        (self.project / ".agents").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            api.install_project(self.project, self.source)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.project / ".osa").exists())
        (self.project / ".agents").unlink()
        (self.source / "hooks/outside").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            api.install_project(self.project, self.source)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_refuses_user_data_added_to_installed_payload(self):
        api = self.installer()
        api.install_project(self.project, self.source)
        user_file = self.project / ".osa/pack/user.txt"
        user_file.write_text("Keep this\n")
        with self.assertRaises(ValueError):
            api.install_project(self.project, self.source)
        self.assertEqual(user_file.read_text(), "Keep this\n")

    def test_doctor_detects_changed_anchor_and_discovery(self):
        api = self.installer()
        api.install_project(self.project, self.source)
        (self.project / "AGENTS.md").write_text("Only user rules\n")
        link = self.project / ".agents/skills/poteto-mode"
        link.unlink()
        result = api.doctor_project(self.project)
        self.assertFalse(result["ok"])
        self.assertTrue(any("AGENTS.md" in issue for issue in result["issues"]))
        self.assertTrue(any(".agents/skills/poteto-mode" in issue for issue in result["issues"]))

    def test_host_changes_remove_only_owned_discovery_links(self):
        api = self.installer()
        first = api.install_project(self.project, self.source)
        self.assertEqual(first["level"], "ultra")
        custom = self.project / ".claude/commands/custom.md"
        custom.write_text("User command\n")
        second = api.install_project(self.project, self.source, hosts=("codex",))
        self.assertEqual(second["hosts"], ["codex"])
        self.assertFalse((self.project / ".claude/skills/poteto-mode").is_symlink())
        self.assertEqual(custom.read_text(), "User command\n")
        self.assertTrue(api.doctor_project(self.project)["ok"])

    def test_refuses_complete_unowned_markers_and_nested_source(self):
        api = self.installer()
        original = "<!-- OSA:BEGIN -->\nUser text\n<!-- OSA:END -->\n"
        (self.project / "AGENTS.md").write_text(original)
        with self.assertRaises(ValueError):
            api.install_project(self.project, self.source)
        self.assertEqual((self.project / "AGENTS.md").read_text(), original)
        self.assertFalse((self.project / ".osa").exists())
        with self.assertRaises(ValueError):
            api.install_project(self.source / "nested project", self.source)
        self.assertFalse((self.source / "nested project").exists())

    def test_off_anchor_resolves_mode_before_automatic_activation(self):
        api = self.installer()
        api.install_project(self.project, self.source, level="off")
        text = (self.project / "AGENTS.md").read_text()
        self.assertIn("Before activation", text)
        self.assertIn("If the resolved mode is `off`, skip automatic workflow and token activation.", text)
        self.assertLess(text.index("Before activation"), text.index("select the skills"))

    def test_failed_anchor_write_is_unhealthy_and_retry_repairs(self):
        api = self.installer()
        original = Path.write_text

        def fail_anchor(path, *args, **kwargs):
            if path.name == "AGENTS.md":
                raise OSError("Simulated anchor write failure")
            return original(path, *args, **kwargs)

        with patch.object(Path, "write_text", fail_anchor), self.assertRaises(OSError):
            api.install_project(self.project, self.source)
        self.assertFalse(api.doctor_project(self.project)["ok"])
        api.install_project(self.project, self.source)
        self.assertTrue(api.doctor_project(self.project)["ok"])


if __name__ == "__main__":
    unittest.main()
