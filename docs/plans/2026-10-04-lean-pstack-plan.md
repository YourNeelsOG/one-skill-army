# Lean pstack integration plan

Approved design: option 2 in the current conversation on 2026-10-04.
Poteto becomes OSA's default workflow with on-demand detailed resources.
Public skill paths and all 50 pinned workflows remain available.

## Checklist

- [x] Read the poteto-mode Principles section.
- [x] Phase A: Frame. Audit integration, duplication, and existing changes.
- [x] Phase B: Design the workflow. User approved option 2.
- [x] Phase C: Run the loop.
- [x] Add preservation and policy reachability checks. Observe failures before edits.
- [x] Centralize repeated imported policy and lookup sections in the shared runtime.
- [x] Split the poteto entrypoint into a compact router and detailed references.
- [x] Route OSA to poteto by default. Correct host invocation documentation.
- [x] Phase D: Keep the audit trail. Record decisions and their evidence locally.
- [x] Phase E: Verify and hand back. Check isolated installs, full Python tests,
      structural checks, resource closure, preserved workflows, and text size.

## Verification boundaries

Capture pre-change workflow bodies locally and compare preserved workflow text.
Keep provenance, licenses, script resources, and model configuration intact.
Use isolated installation destinations. Do not update live host installations.
Measure bytes and words as instruction-size evidence, not billing savings.
Review each completed unit before continuing. No external delivery is authorized.

## Verified evidence

- 199 unittest executions passed, including isolated installation and resource closure.
- All structural checks passed. Host reminder test observed RED before GREEN.
- Detailed poteto workflow hash preserved after normalizing relocated links.
- 105 other original Markdown bodies matched after removing shared headers.
- Isolated installer doctor, bundled brief, and real session hook JSON passed.
- Imported entrypoints are 38.0% smaller in UTF-8 source bytes.
- Live host installation was not updated. Runtime billing savings are unmeasured.
- In-session review restored original how, architect, and pre-commit trigger scopes.
