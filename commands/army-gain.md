---
description: "Measured-impact scoreboard for One Skill Army in THIS repo. Honest numbers only, never invented baselines."
---

Show One Skill Army's measured impact in this repository. One-shot display;
change no mode, write no files.

## The Iron Rule

NEVER invent a savings number. The unbuilt version was never written, so
there is no baseline to subtract from. Report only figures that were counted:

1. **Debt ledger**: run the `/army-debt` scan. Report: `<N> osa: markers,
   <M> with no upgrade trigger (rot risk).`
2. **Cuttable now**: if a fresh `/army-audit` was run this session, report
   its `net: -<N> lines, -<M> deps possible.` If not, say audit not yet run
   this session and offer it; do not estimate from memory.
3. **Diff effect**: if the user names a commit range, report the diffstat
   delta actually computed by git (`git diff --shortstat`), labeled as what
   changed, not what was "saved".

## Pack-level benchmarks

One Skill Army has no published benchmark medians of its own yet. Do NOT
quote another project's numbers as if they were ours. If the user asks what
the pack saves in general, answer qualitatively (less code, fewer tokens,
same safety) and point at the three measured sources above.

## Output shape

```
army gain: <repo>

  debt:      <N> osa: markers, <M> no-trigger
  cuttable:  -<N> lines, -<M> deps   (from /army-audit this session, or "not run")
  diff:      <shortstat if a range was given, else "no range given">
  overhead:  pack injects ~<k> tokens/session (skills + hooks); terse mode
             pays off only when output waste exceeds that

  honest? every number above was counted, none estimated.
```

If the session was short, the work already terse, or billing is
per-request/credit: say the pack is likely net-negative for this workload
and suggest `/army off`. Hiding a net-negative regime behind a gross number
is the one dishonesty this command exists to prevent.
