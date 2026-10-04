"""Exercise the npm distribution from a packed copy outside the checkout."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestNpmInstall(unittest.TestCase):
    """Check the user-facing launcher, package contents, and Python boundary."""

    def test_packed_launcher_installs_and_checks_a_project(self):
        """A release archive must work without access to this source checkout."""
        self.assertTrue((ROOT / 'package.json').is_file(), 'npm distribution is missing')
        with tempfile.TemporaryDirectory(prefix='osa npm ') as temporary:
            base = Path(temporary)
            environment = dict(os.environ, npm_config_cache=str(base / 'cache'))
            result = subprocess.run(
                ['npm', 'pack', '--json', '--ignore-scripts', '--pack-destination', str(base)],
                cwd=ROOT, env=environment, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            metadata = json.loads(result.stdout)
            package = metadata[0] if isinstance(metadata, list) else metadata['@yourneelsog/one-skill-army']
            files = {item['path'] for item in package['files']}
            self.assertIn('bin/osa.mjs', files)
            self.assertIn('osa/install.py', files)
            self.assertIn('skills/poteto-mode/SKILL.md', files)
            self.assertFalse(any(name.startswith(('.osa/', 'tests/', '.git/')) for name in files))
            self.assertFalse(any('/node_modules/' in name or '/__pycache__/' in name for name in files))
            self.assertFalse(any(Path(name).name.startswith('.env') for name in files))
            archive = base / package['filename']
            shutil.unpack_archive(str(archive), str(base / 'unpacked'), 'gztar')
            launcher = base / 'unpacked/package/bin/osa.mjs'
            project = base / 'new project'
            project.mkdir()
            command = ['node', str(launcher)]
            for arguments in (['install', '.', '--level', 'ultra'], ['doctor', '.']):
                result = subprocess.run(command + arguments, cwd=project,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            anchor = (project / 'AGENTS.md').read_text()
            self.assertIn('automatically', anchor.lower())
            self.assertIn('ultra', anchor)
            self.assertTrue((project / '.agents/skills/poteto-mode/SKILL.md').is_file())
            result = subprocess.run(command + ['version'], cwd=project,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), '2.2.0')

    def test_launcher_reports_a_missing_python_runtime(self):
        """An absent prerequisite gives a useful error rather than a silent failure."""
        launcher = ROOT / 'bin/osa.mjs'
        self.assertTrue(launcher.is_file(), 'npm launcher is missing')
        environment = dict(os.environ, OSA_PYTHON='/nonexistent/osa-python')
        result = subprocess.run(['node', str(launcher), 'version'], env=environment,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Python 3', result.stderr)

    def test_launcher_uses_its_package_when_the_project_has_an_osa_module(self):
        """A project module with the same name must not shadow the installed CLI."""
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'osa.py').write_text("raise RuntimeError('project module was imported')\n")
            result = subprocess.run(['node', str(ROOT / 'bin/osa.mjs'), 'version'],
                                    cwd=project, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), '2.2.0')


if __name__ == '__main__':
    unittest.main()
