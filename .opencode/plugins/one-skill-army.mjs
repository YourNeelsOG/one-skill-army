// One Skill Army - OpenCode plugin.
//
// Registers the pack's skills + commands and re-injects a one-line reminder
// into the system prompt every turn (drift guard). Add to opencode.json:
//   { "plugin": ["one-skill-army@git+https://github.com/YourNeelsOG/one-skill-army.git"] }
// or, for a local checkout, copy/symlink this file into
//   ~/.config/opencode/plugins/  (global) or <project>/.opencode/plugins/ (project)
//
// Mode resolution mirrors hooks/session-start: OSA_DEFAULT_MODE env >
// defaultMode in <repo>/.osa/config.json > full. "off" disables injection.

import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const REMINDER =
  'One Skill Army active: ladder before code (does it need to exist? can it be shorter and still do the same work?), terse prose (never terse facts), read the smallest thing that answers, verify before claiming done, no em dashes, git-safety rails hold. Levels: lite/full/ultra/off only.';

// Decode the module URL before resolving paths containing spaces or Unicode.
function repoRoot() {
  return process.env.OSA_REPO_ROOT || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
}

function readMode() {
  try {
    const env = process.env.OSA_DEFAULT_MODE;
    if (env) return env.trim().toLowerCase();
  } catch (e) {}
  try {
    const cfg = JSON.parse(fs.readFileSync(path.join(process.cwd(), '.osa', 'config.json'), 'utf8'));
    if (cfg && typeof cfg.defaultMode === 'string') return cfg.defaultMode.trim().toLowerCase();
  } catch (e) {}
  return 'ultra';
}

function parseCommandFile(file) {
  try {
    const text = fs.readFileSync(file, 'utf8');
    const m = text.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    if (!m) return null;
    const desc = (m[1].match(/^description:\s*"?(.+?)"?\s*$/m) || [])[1] || '';
    return { description: desc, prompt: m[2].trim(), agent: 'build' };
  } catch (e) {
    return null;
  }
}

export default async () => {
  const root = repoRoot();
  return {
    config: async (config) => {
      // Register slash commands from the pack's commands/ directory.
      if (!config.command) config.command = {};
      try {
        const cmdDir = path.join(root, 'commands');
        for (const f of fs.readdirSync(cmdDir).filter((x) => x.endsWith('.md'))) {
          const parsed = parseCommandFile(path.join(cmdDir, f));
          if (parsed) config.command[path.basename(f, '.md')] = parsed;
        }
      } catch (e) {}
      // Register the complete installed skills directory.
      try {
        const skillsDir = path.join(root, 'skills');
        if (fs.existsSync(skillsDir)) {
          config.skills = config.skills || {};
          config.skills.paths = config.skills.paths || [];
          if (!config.skills.paths.includes(skillsDir)) config.skills.paths.push(skillsDir);
        }
      } catch (e) {}
    },

    // Append the reminder to the system prompt every turn.
    'experimental.chat.system.transform': async (_input, output) => {
      try {
        if (readMode() === 'off') return;
        if (output && Array.isArray(output.system)) {
          output.system.push(REMINDER);
        }
      } catch (e) {}
    },
  };
};
