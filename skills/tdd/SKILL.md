---
name: tdd
description: "Mandatory failing-test-first workflow for production changes, bug fixes, features, refactors, and executable helpers. Use for /tdd and implementation work."
---

# TDD


## OSA execution contract

Read [portable runtime and policy](../poteto-mode/references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.

Apply to every production change, including new behavior, bug fixes, refactors, and executable helpers. OSA's failing-test-first rule is mandatory.

## Workflow

1. Read the affected files and callers. For a defect, reproduce it and trace the cause before choosing a fix.
2. State the approved behavior and choose the smallest observable input and expected output. Use the repository's real public interface and existing test runner.
3. Write one minimal behavioral test before production edits. Run it and observe RED for the intended reason. A syntax error, missing dependency, or broken fixture is not the intended failure.
4. If RED is unavailable, stop production edits and resolve the test prerequisite under the approved scope. A deterministic browser test, integration assertion, or regression script can be a test if it executes the real behavior and fails loudly. A verbal repro or code inspection cannot replace RED.
5. Write the least production code that passes the test. Keep boundary validation, error handling, authorization, and required purpose comments.
6. Run the test GREEN. Refactor only while green. Run relevant surrounding checks and, where applicable, exercise the same user path that originally failed.
7. Inspect the final diff and report the exact failing-before and passing-after evidence. Never weaken assertions to conceal wrong behavior.

## Refactors and corrections

Pin existing behavior with characterization checks. Before a production structural edit, add a failing check for the intended invariant or missing guarantee, then retain the behavioral pin throughout the move. Keep expected values independent of the implementation. If a flaky test cannot reliably expose the issue, make the failure deterministic before fixing production.

Production code written before RED must be removed and reintroduced only after RED. Preserve unrelated work. No selective-TDD escape applies when tests are expensive or inconvenient.

## Reply

Name the RED test, its observed failure, the GREEN run, and surrounding verification. State any unresolved prerequisite and do not claim production completion when failing-before evidence is absent.
