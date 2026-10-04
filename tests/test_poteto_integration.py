"""Verify the complete poteto skill pack installs as usable OSA workflows."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMPORTED = """architect arena automate-me benchmark-checklist blast-radius bro
correct create-verification-skill figure-it-out how interrogate
maintain-verification-skill make-bot-ui no-comments poteto-mode
principle-attack-the-premise principle-boundary-discipline
principle-build-the-lever principle-encode-lessons-in-structure
principle-exhaust-the-design-space principle-experience-first
principle-explain-the-number principle-fix-root-causes
principle-foundational-thinking principle-guard-the-context-window
principle-laziness-protocol principle-make-operations-idempotent
principle-migrate-callers-then-delete-legacy-apis principle-minimize-reader-load
principle-model-the-domain principle-never-block-on-the-human
principle-outcome-oriented-execution principle-prove-it-works
principle-redesign-from-first-principles
principle-separate-before-serializing-shared-state
principle-sequence-verifiable-units principle-subtract-before-you-add
principle-test-behavior-not-implementation principle-type-system-discipline
recall reflect setup-pstack show-me-your-work swarm tdd teach technical-writing
typescript-best-practices unslop why""".split()


class TestPotetoIntegration(unittest.TestCase):
    """Exercise source inventory, installed resources, and host discovery."""

    def test_complete_pinned_inventory_with_attribution(self):
        provenance = json.loads((ROOT / "skills/poteto-mode/provenance.json").read_text())
        self.assertEqual(provenance["revision"], "e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a")
        self.assertEqual(set(provenance["skills"]), set(IMPORTED))
        for name in IMPORTED:
            directory = ROOT / "skills" / name
            self.assertTrue((directory / "SKILL.md").is_file(), name)
            self.assertIn("Copyright (c) 2026 Lauren Tan", (directory / "LICENSE").read_text())

    def test_plugin_resource_paths_exist(self):
        for path in ROOT.glob(".*-plugin/plugin.json"):
            manifest = json.loads(path.read_text())
            for key in ("skills", "commands", "agents", "instructions", "hooks"):
                if key in manifest:
                    self.assertTrue((ROOT / manifest[key]).exists(), f"{path.name}: {key}")

    def test_installed_pack_is_complete_and_repeatable(self):
        with tempfile.TemporaryDirectory(prefix="osa install ") as tmp:
            base = Path(tmp)
            for attempt in range(2):
                result = subprocess.run(["bash", str(ROOT / "scripts/install.sh"),
                                         "--dir", tmp], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for name in IMPORTED:
                directory = base / "skills" / name
                self.assertTrue((directory / "SKILL.md").is_file(), name)
                self.assertTrue((directory / "LICENSE").is_file(), name)
                command = (base / "commands" / (name + ".md")).read_text()
                self.assertIn(name + "/SKILL.md", command)
                self.assertIn("$ARGUMENTS", command)
                for document in directory.rglob("*.md"):
                    for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
                        if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                            continue
                        target = target.split("#", 1)[0]
                        if not target or any(char in target for char in "<> *`"):
                            continue
                        resolved = document.parent / target
                        self.assertTrue(resolved.exists(), f"{document.relative_to(base)}: {target}")
            doctor = subprocess.run(["bash", str(ROOT / "scripts/install.sh"),
                                     "--dir", tmp, "--doctor"], capture_output=True, text=True)
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            (base / "skills/poteto-mode/SKILL.md").unlink()
            doctor = subprocess.run(["bash", str(ROOT / "scripts/install.sh"),
                                     "--dir", tmp, "--doctor"], capture_output=True, text=True)
            self.assertNotEqual(doctor.returncode, 0)
            self.assertIn("poteto-mode", doctor.stdout)

    def test_opencode_discovers_commands_without_environment_override(self):
        script = """import plugin from './.opencode/plugins/one-skill-army.mjs';
const hooks = await plugin();
const config = {};
await hooks.config(config);
console.log(JSON.stringify(config));
"""
        environment = dict(os.environ)
        environment.pop("OSA_REPO_ROOT", None)
        result = subprocess.run(["node", "--input-type=module", "-e", script],
                                cwd=ROOT, env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads(result.stdout)
        self.assertIn(str(ROOT / "skills"), config.get("skills", {}).get("paths", []))
        for name in IMPORTED:
            self.assertIn(name, config["command"])

    def test_copy_failure_does_not_record_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            binaries = base / "bin"
            binaries.mkdir()
            fake_copy = binaries / "cp"
            fake_copy.write_text("#!/bin/sh\nexit 9\n")
            fake_copy.chmod(0o755)
            environment = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ["PATH"])
            target = base / "install"
            result = subprocess.run(["bash", str(ROOT / "scripts/install.sh"),
                                     "--dir", str(target)], env=environment,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertFalse((target / ".one-skill-army-version").exists())

    def test_installer_rejects_a_destination_inside_its_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(ROOT / "scripts", source / "scripts")
            sentinel = source / "skills/one-skill-army/SKILL.md"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text("source must survive\n")
            result = subprocess.run(["bash", str(source / "scripts/install.sh"),
                                     "--dir", str(source)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(), "source must survive\n")

    def test_zcode_install_preserves_config_and_registers_complete_pack(self):
        self.assertIn("OSA_ZCODE_BASE", (ROOT / "scripts/install-zcode.sh").read_text(),
                      "Do not run the installer before it supports isolated destinations")
        with tempfile.TemporaryDirectory(prefix="osa zcode ") as tmp:
            base = Path(tmp) / "zcode"
            agents = Path(tmp) / "agents"
            config = base / "cli/config.json"
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({"existing": {"preserve": True}}))
            environment = dict(os.environ, OSA_ZCODE_BASE=str(base), OSA_AGENTS_BASE=str(agents))
            command = ["bash", str(ROOT / "scripts/install-zcode.sh")]
            for attempt in range(2):
                result = subprocess.run(command + ["--agents-compat"], env=environment,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            content = json.loads(config.read_text())
            self.assertEqual(content["existing"], {"preserve": True})
            for event in ("SessionStart", "UserPromptSubmit"):
                hooks = [hook for group in content["hooks"]["events"][event] for hook in group["hooks"]]
                self.assertEqual(len(hooks), 1, event)
            for name in IMPORTED:
                self.assertTrue((base / "skills" / name / "SKILL.md").exists(), name)
                self.assertTrue((agents / "skills" / name / "SKILL.md").exists(), name)
            result = subprocess.run(command + ["--doctor"], env=environment,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run(command + ["--uninstall"], env=environment,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(config.read_text()), {"existing": {"preserve": True}})
            for name in IMPORTED:
                self.assertFalse((base / "skills" / name).exists(), name)
                self.assertFalse((agents / "skills" / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
