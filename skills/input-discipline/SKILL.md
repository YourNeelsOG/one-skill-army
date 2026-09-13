---
name: input-discipline
description: >
  Use when reading files, scanning logs, exploring an unfamiliar codebase,
  delegating search, or when context grows large. Saves INPUT tokens: grep
  before reading, read ranges not whole files, quote the decisive line,
  delegate broad exploration to a cheap subagent, never let tool output
  flood the context. Pairs with token-discipline (which saves OUTPUT tokens).
---

# Input Discipline

Token-discipline compresses what you write. This compresses what you take
in. Context is the budget that silently dies: every token you read gets
re-paid on every later turn until compaction.

## The Iron Law

```
READ THE SMALLEST THING THAT ANSWERS THE QUESTION
```

Never make the agent dumber to save tokens: trimmed context must leave a
working recall path (see memory). If you cannot afford to read what a task
needs, say so; do not squint.

## Read discipline

1. **Locate before you read.** Grep/Glob for the symbol, error string, or
   route first. Read the file only after you know it is the right file.
2. **Read ranges, not files.** Grep gives `path:line`; read +/-40 lines around
   it. Whole-file reads are for files under ~100 lines or when rewriting the
   whole file.
3. **Never paste big output back.** A 500-line log is not evidence; the 3
   lines around the stack trace are. Quote the shortest decisive line, cite
   `path:line` for the rest.
4. **Prefer structured queries.** `grep -c`, `git log --oneline -10`,
   `ls`, `wc -l` over dumps. Count first, sample second, read last.
5. **One retry, then change the query.** Re-running the same broad read
   hoping for a smaller result is not a strategy.

## Tool output discipline

- Long-running or noisy command? Pipe through `tail -n 50`, `grep -i error`,
  or redirect to a file and grep it.
- Test suites: run the focused subset first (`pytest tests/test_x.py`),
  full suite only at verification time.
- JSON: query it (`jq '.field'`), do not cat it.

## Delegate broad exploration

Cold-start orientation or cross-file localization ("where does X happen?",
"what calls Y?") with no named file: dispatch a cheap, read-only subagent
instead of exploring in main context. Its contract (FastContext pattern):

- Read/Glob/Grep only; no edits, no opinions.
- Fan out several parallel searches on the first turn.
- Reply is ONLY an evidence block, one citation per line:
  `path/to/file.ext:START-END  why relevant`
- Cites only ranges it actually read. Never invents or estimates a range.
- Found nothing? Reply exactly: "no relevant locations found". That honest
  answer beats a guess.

The solver reads the citations and nothing else, so the exploration's reads
never enter main context.

## Rationalizations

| Excuse | Reality |
|--------|----------|
| "I'll just read the whole file to be safe" | Be safe with a range + grep. Whole-file reads compound for the rest of the session. |
| "The log might have something relevant" | Grep it. "Might" is what search is for. |
| "Subagent dispatch is overhead" | So is 10k tokens of exploration in main context, except that cost repeats every turn. |
| "I already read it once" | Context still pays for it every turn. Cite path:line and re-read ranges on demand. |
| "Quoting the full error is more accurate" | Quote the decisive line exactly, cite the rest. Accuracy lives in the line, not the volume. |

## Boundaries

Never applies to: files you are about to fully rewrite, verification output
you must read completely before claiming success (verification-before-
completion wins), or security-relevant code where partial reads invite
hallucinated claims (anti-hallucination wins). Input-discipline chooses HOW
to read; it never skips a read the other disciplines require. "stop
input-discipline" / "normal mode": revert.
