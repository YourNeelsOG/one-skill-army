---
description: "Whole-repo audit: reinvented wheels, dead code, dependency sprawl, unverified assumptions. One line per finding, reads only."
---

Audit the repository (or the paths in $ARGUMENTS). Reads and reports,
changes nothing.

## Scan

1. **Reinvented wheels**: custom implementations of stdlib / native-platform
   features (date pickers, debounce, deep clone, modals, HTTP wrappers).
2. **Dead or speculative code**: exports with no callers, config with one
   consumer, abstractions with one implementation.
3. **Dependency sprawl**: packages duplicating stdlib, platform APIs, or
   each other. Flag each with what replaces it.
4. **Unverified assumptions**: TODOs, comments asserting behavior no test
   covers, docs referencing files that don't exist.
5. **Comment hygiene**: `osa:` markers with no upgrade trigger (rot risk),
   em dashes, banner comments.

## Output

One line per finding, same tags as `/army-review`:
`<file>:L<line>: <tag> <what>. <replacement>.`

End with: `<N> findings. net: -<M> lines possible. <K> osa: markers, <J> with no trigger.`

Then a proposed minimal-change plan (deletions first), for approval. Do not
modify anything until approved.
