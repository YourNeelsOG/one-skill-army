# Poteto mode integration plan

Approved design: ../specs/2026-10-04-poteto-mode-design.md.

1. Establish failing integration tests in tests/test_poteto_integration.py:
   full inventory, license and provenance, local references, packaged commands,
   temporary installation/upgrade/doctor, and OpenCode path discovery.
2. Import and adapt the 50 pinned skill directories under skills/. Preserve
   complete workflows and helpers; rewrite conflicting authority and unavailable
   host assumptions. Verify source inventory and scan every imported file.
3. Integrate scripts/pack-manifest.sh, commands/, and
   skills/one-skill-army/SKILL.md. Fix OpenCode discovery as covered by its
   failing test. Verify temporary copy-based installs and idempotence.
4. Synchronize README.md, adapters/, manifests, and osa/__init__.py. Rebuild
   skills/one-skill-army/osa.pyz and run all repository test scripts.
5. Run optional Bun helper tests in temporary storage. Independently exercise
   read-only investigation, bug-fix/verification routing, and permission-boundary
   scenarios with the adapted skills. Review actual artifacts, correct defects,
   refresh the osa graph, and write a sourced memory handoff.

Each step is complete only with fresh verification evidence. Remote mutations
and real host installs are outside this implementation's authorization.

## Verification completed, 2026-10-04

- Repository suite: 195 unittest executions and 304 structural checks passed.
- All 50 imported skills passed the skill-creator frontmatter validator.
- Isolated install, repeat install, doctor, uninstall, installed resource links,
  plugin resources, copy failure, source overlap, and OpenCode paths passed.
- Optional helpers: 53 Bun tests, 210 assertions, strict TypeScript check,
  three Node shell regressions, and shell syntax checks passed in temporary storage.
- Representative investigation, RED/GREEN bug fix, generated verification
  skill, and documented CLI checks exercised in disposable fixtures.
- Live authenticated provider operations and every host runtime remain unverified.
- Test-isolation incident: an early ZCode test touched live installation paths.
  Imported entries were removed; baseline pack restored from repository HEAD
  and configuration from the first automatic backup. Prior installed-file
  customizations cannot be reconstructed. Explicit path overrides and a test
  preflight now prevent that regression.
