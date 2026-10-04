---
name: setup-pstack
description: Configure which models pstack uses per role and at what reasoning budget. Detects your available models and writes an always-applied rule that overrides the skill defaults. Use for /setup-pstack, "configure pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack model roles for OSA


## OSA execution contract

Read [portable runtime and policy](../poteto-mode/references/runtime.md) before acting.
Reuse it once per task unless it changes or context is compacted.

Configure optional model choices for the imported workflows. Store project-local choices in `.osa/poteto-models.json`. The name remains `/setup-pstack` for compatibility. No Cursor rule or global host configuration is required.

## Steps

1. Discover actual delegation capabilities and the model identifiers the current host exposes. Read their schemas. If enumeration is unavailable, default every role to `inherit-parent` and report that model entitlement is unverified. User-provided identifiers are preferences to validate, not proof of availability.
2. Read existing `.osa/poteto-models.json` when present. Validate `version`, `budget`, and `roles`. Keep valid role choices, flag malformed entries, and list retired roles before proposing removal. Never execute strings from the file.
3. Ask for a cost preference only if the task does not establish one: inherited defaults, conservative cost, or broader available-model diversity. Budget labels describe a preference; they do not promise billing or map OSA's lite/full/ultra/off intensity to model reasoning. Apply reasoning settings only through supported separate host parameters. Never fabricate a model identifier by adding suffixes.
4. Show every role and its selected identifier, plus unavailable choices and the fallback. Scalar roles are `feature, refactoring`, `bug-fix`, `perf-issue`, `hillclimb`, `judgment and prose`, `hardest tasks`, `how explorer`, `how explainer`, `why investigators`, `why synthesizer`, `reflect tooling`, `reflect judgment, divergent, synthesizer`, and `swarm workers`. Panel roles are `arena runners`, `arena cross-judge pool`, `architect runners`, and `interrogate reviewers`. Panel entries can repeat `inherit-parent`; they remain separate roles, not independent model families.
5. Present the configuration design and obtain approval before writing. Use only identifiers confirmed available or the aliases `inherit-parent` and `auto`. When the host forbids model overrides, use inherit even if an identifier exists. Write the complete JSON idempotently, preserving unrelated files.
6. Re-read and parse the written configuration. Verify a supported role invocation only if it is authorized and available. Otherwise verify JSON shape and report runtime validation unavailable. Missing or rejected roles fall back to inherit with a visible limitation.
7. Check for a project verification skill or real application driver. If absent, describe `/create-verification-skill` as the available follow-up. Do not create adaptive or personal skills until the user defines and approves them.

## Example shape

```json
{
  "version": 1,
  "budget": "inherited defaults",
  "roles": {
    "feature, refactoring": "inherit-parent",
    "judgment and prose": "inherit-parent",
    "arena runners": ["inherit-parent", "inherit-parent"],
    "arena cross-judge pool": ["inherit-parent"],
    "architect runners": ["inherit-parent", "inherit-parent"],
    "interrogate reviewers": ["inherit-parent", "inherit-parent"]
  }
}
```

## Reply

State the written path, validated roles, actual capability checks, and fallback limits. Never claim host-wide activation, new-session injection, independent consensus, or a measured cost saving without evidence.
