---
name: principle-fix-root-causes
description: "Apply when debugging. Trace each symptom to its root cause and fix it there; reproduce first, ask why until you reach it, resist nil-check guards that silence crashes."
---

# Fix Root Causes


## OSA execution contract

Read [portable runtime and policy](../poteto-mode/references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.

When debugging, do not fix symptoms. Trace every problem to its root cause and fix it there.

**Why:** Symptom fixes accumulate. Each workaround makes the system harder to reason about, and the real bug remains. Root-cause fixes are slower upfront but reduce total debugging time.

**Pattern:**
- Reproduce first
- Ask "why" until you hit the root cause
- Do not add a guard merely to hide a broken invariant. Keep or add required trust-boundary validation, authorization, and error handling.
- A long workaround explanation is a reason to inspect the design. Preserve real constraints and required WHY comments while investigating a smaller root-cause fix.
- Check for the pattern, not just the instance (grep for the same pattern, fix all instances)
- When stuck, instrument. Don't guess (add logging, read the actual error)

**Restart bugs: suspect state before code**

When something "fails after restart," suspect stale persistent state first: config files, caches, lock files, serialized state. If clearing a state file restores behavior, prioritize state validation as the fix.
