// Verify dependency checks never launch an implicit installer or write runtime files.
import { test, expect } from "bun:test";
import { mkdtempSync, copyFileSync, writeFileSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

test("missing dependencies require explicit setup without launching Bun install", async () => {
  const directory = mkdtempSync(join(tmpdir(), "osa-bootstrap-"));
  copyFileSync(join(import.meta.dir, "bootstrap.ts"), join(directory, "bootstrap.ts"));
  copyFileSync(join(import.meta.dir, "package.json"), join(directory, "package.json"));
  copyFileSync(join(import.meta.dir, "bun.lock"), join(directory, "bun.lock"));
  writeFileSync(join(directory, "probe.ts"), `
import { ensureDependenciesInstalled } from "./bootstrap.ts";
Bun.spawnSync = (() => { console.log("IMPLICIT_INSTALL"); return {exitCode: 1, stdout: new Uint8Array(), stderr: new Uint8Array()}; }) as typeof Bun.spawnSync;
try { ensureDependenciesInstalled(); } catch (error) { console.error(String(error)); process.exitCode = 1; }
`);
  try {
    const result = Bun.spawnSync([process.execPath, join(directory, "probe.ts")]);
    expect(result.exitCode).toBe(1);
    expect(result.stdout.toString()).not.toContain("IMPLICIT_INSTALL");
    expect(result.stderr.toString()).toContain("bun install --frozen-lockfile");
    expect(readdirSync(directory)).not.toContain("node_modules");
  } finally { rmSync(directory, { recursive: true, force: true }); }
});
