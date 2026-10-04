// Check optional Bun helper dependencies without installing packages implicitly.
import { existsSync } from "node:fs";
import { join } from "node:path";

// Keep setup explicit so even --help cannot modify an installed skill directory.
export function ensureDependenciesInstalled(): void {
  const scriptsDirectory = import.meta.dir;
  if (!existsSync(join(scriptsDirectory, "node_modules", "commander", "package.json"))) {
    throw new Error(
      `Optional helper dependencies are missing. In ${scriptsDirectory}, run bun install --frozen-lockfile before using Bun helpers.`
    );
  }
}
