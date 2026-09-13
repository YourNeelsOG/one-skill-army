---
description: "Harvest every osa: marker into a debt ledger so deliberate shortcuts get tracked instead of rotting."
argument-hint: "[optional: paths]"
---

Every deliberate minimal-code shortcut is marked with an `osa:` comment
naming its ceiling and upgrade path. This collects them into one ledger so a
deferral can't quietly become permanent.

Scope: $ARGUMENTS (empty = whole repo).

## Scan

Grep the repo, skipping `node_modules`, `.git`, and build output:

`grep -rnE '(#|//) ?osa:' .` (add other comment prefixes your stack uses)

Each hit is one ledger row. The comment prefix keeps prose that merely
mentions the convention out of the ledger.

## Output

One row per marker, grouped by file:

`<file>:<line>, <what was simplified>. ceiling: <the limit named>. upgrade: <the trigger to revisit>.`

Pull the ceiling and the trigger straight from the comment. Flag rot risk:
any `osa:` marker naming no upgrade trigger gets a `no-trigger` tag; those
are the ones that silently rot.

End with: `<N> markers, <M> with no trigger.`
Nothing found: `No osa: debt. Clean ledger.`

## Boundaries

Reads and reports only. To persist, ask, and it writes the ledger to a file
(e.g. `OSA-DEBT.md`). One-shot.
