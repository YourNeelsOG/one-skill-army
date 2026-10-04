#!/usr/bin/env node
// Launch the bundled Python engine from npm while retaining the user's project directory.
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const packageRoot = fileURLToPath(new URL('../', import.meta.url));
const python = process.env.OSA_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
// `python -m osa` puts the working directory first on sys.path, so a project file
// named osa.py would shadow the engine. Replace that entry with the package root.
const bootstrap = 'import runpy, sys; sys.path[0] = sys.argv.pop(1); '
  + 'runpy.run_module("osa", run_name="__main__", alter_sys=True)';
const child = spawn(python, ['-c', bootstrap, packageRoot, ...process.argv.slice(2)], {
  stdio: 'inherit',
});

// A missing prerequisite must produce an actionable error and a failing exit status.
child.on('error', (error) => {
  process.stderr.write(`OSA requires Python 3. Install it or set OSA_PYTHON to its executable. ${error.message}\n`);
  process.exitCode = 1;
});
child.on('exit', (code, signal) => {
  process.exitCode = code ?? (signal ? 1 : 0);
});
