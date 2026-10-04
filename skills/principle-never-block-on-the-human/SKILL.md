---
name: principle-never-block-on-the-human
description: "Continue routine work within an approved design while preserving OSA design and per-action approval gates. Use when tempted to ask about an observable fact or already-authorized execution choice."
---

# Never block on routine execution


## OSA execution contract

Read [portable runtime and policy](../poteto-mode/references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.

Proceed autonomously within an explicitly approved design and scope. Use observable evidence to settle routine implementation choices. Present verified results so the human can review them.

## Pattern

- Read current source rather than asking the human for facts tools can establish.
- Resolve routine reversible choices within existing authorization and log meaningful decisions.
- Keep independent approved work moving when one step needs a human decision.
- Investigate recurring failures and propose a concrete root-cause design before widening scope.

## Boundaries

Design approval is required before implementation. Missing approval is a gate, not a bottleneck to bypass. Product direction belongs to the human. External writes, messages, PR creation, review dismissal, merge, deploy, and protected-branch pushes require explicit per-action approval. Never rewrite pushed history. A broad autonomy request never substitutes for these gates.

Report the exact pending action and its reviewable evidence, then wait on dependent work. Do not treat silence as approval.
