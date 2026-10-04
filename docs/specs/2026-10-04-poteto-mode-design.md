# Poteto mode in One Skill Army

Purpose: integrate the complete pstack skill set into OSA, as approved by the
user on 2026-10-04, without replacing the existing OSA disciplines.

## Source and layout

Pin cursor/plugins at e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a, pstack
version 0.15.9. Add its 50 skill directories under skills/, including
skills/poteto-mode/. Keep playbooks, references, scripts, and upstream tests
with their owning skill. Preserve Lauren Tan's MIT notice in each imported
skill so copy-based installs retain attribution. Record source revision,
inventory, and adaptation notes beside poteto-mode.

## Routing and authority

OSA remains the standing policy layer. Poteto mode is a task workflow selected
explicitly or when its capability matches. Every imported skill honors OSA
design approval, mandatory TDD, structural comments, evidence requirements,
and per-action Git and external-write authorization. Review means a human or
an in-session agent, never an external automated reviewer. Shipping prepares
reviewable artifacts before requesting the particular external action.

Expose the imported skills through command wrappers and the existing skill
manifest. Keep references relative to the installed skill directory; use
the host's real tools and available models rather than hard-coded model slugs.
Embed subagent prompts with the skills that need them, so registration of
named agents is optional. Fall back to sequential execution with an explicit
limitation when a host cannot delegate. Read project graphs through mapit;
use feature maps for runtime verification rather than treating them as a
source-dependency graph.

## Helpers and boundaries

The osa Python engine remains standard-library-only. Imported TypeScript
helpers are optional and retain their own Bun/package prerequisites. Their
setup and tests run in an isolated temporary directory for this integration.
Missing host tools, models, authentication, or runtime access are reported,
never treated as successful verification. Optional helper setup must not
install reviewers or mutate remote repositories.

## Integration and verification

Update the shared installer manifest, orchestrator, command discovery,
documentation, and pack version consistently. Test complete skill inventory,
installed command routing and reference closure, attribution, upgrade and
doctor behavior, and OpenCode discovery from paths with spaces. Run the
existing suite and imported helper tests. Exercise representative workflows
in isolated fixtures; report behavioral and host-specific limits honestly.

## Non-goals

No new adaptive skills until the user specifies their behavior. No marketplace
publication, live host/account configuration, external reviewer installation,
Git push, PR creation, merge, deployment, or claim of universal perfection.
