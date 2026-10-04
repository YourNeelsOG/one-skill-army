---
name: principle-boundary-discipline
description: "Apply when wiring validation, error handling, or framework adapters. Concentrate guards at system boundaries (CLI, config, network, external APIs); trust internal types and keep business logic in pure functions."
---

# Boundary Discipline


## OSA execution contract

Read [portable runtime and policy](../poteto-mode/references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.

Place validation, type narrowing, and error handling at system boundaries. Trust internal contracts only after verifying boundary validation and ownership. Business logic lives in pure functions. The shell is thin and mechanical.

**Why:** Scattered validation is noisy, redundant, and gives a false sense of safety. Keep logic out of framework wiring so it can be tested without the framework.

**The pattern:**
- **At boundaries** (CLI args, config files, external APIs, network protocols): validate, return errors, handle defensively.
- **Inside the system:** typed data, error propagation, no re-validation. Trust the types.
- **Across the boundary.** Expose domain concepts, not the boundary's private representation. Keep general-purpose mechanism inside and special-purpose policy at the edge.

**Applications:**

Validation and error handling:
- Validate config at parse time (the boundary), not inside business logic
- Parse raw data into domain types at the boundary
- Do not re-export transport, storage, framework, or wire types through the public surface
- No redundant nil checks deep in call chains if the boundary already validated

Code organization:
- Business logic in pure functions with no framework dependencies
- Parse functions: pure transforms from raw bytes to typed state
- Prompt construction: structured state in, string out
- Scoring and assessment: pure transforms from state to results

**The tests:**
- "Is this data crossing a trust boundary, or can mutation invalidate an earlier check?" Remove repeated validation only when the actual contract and ownership make it redundant.
- "Can this be a pure function that the shell just calls?" If yes, extract it.
