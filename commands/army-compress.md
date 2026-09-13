---
description: "Compress a natural-language file (AGENTS.md, CLAUDE.md, memory, todos) to terse format for input-token savings. Code files are never touched. Backup kept out of tree."
argument-hint: "<filepath>"
---

Compress the file named in $ARGUMENTS (required; no argument: ask for the
path) into terse style to cut INPUT tokens every session that loads it.
Measured reference class: ~46% average reduction on memory-style files.

## Iron rules

1. Only natural-language files: .md, .txt, .tex, extensionless prose. NEVER
   .py .js .ts .json .yaml .toml .env .lock .css .html .sql .sh or any code.
   Mixed file: compress prose only. Unsure? Leave it unchanged.
2. Backup FIRST, out of tree: copy the original to
   `.osa/backups/<filename>.original.md` before overwriting, so skill
   auto-loaders never re-ingest the backup as a live instruction file.
3. Net-token-negative gate: after writing, recount the file. If the new file
   is not smaller than the original, restore the backup and report failure.

## Remove

Articles (a/an/the), filler (just/really/basically/actually/simply),
pleasantries, hedging ("it might be worth"), connective fluff (however/
furthermore), redundant phrasing ("in order to" to "to", "make sure to" to
"ensure").

## Preserve EXACTLY, never modify

- Fenced code blocks and indented code: read-only regions, copied byte for
  byte. Do not remove comments, spacing, or lines; do not merge around them.
- Inline `backtick content`
- URLs, markdown links, file paths, commands, flags
- Technical terms, library/API names, proper nouns
- Dates, versions, numbers, environment variables
- All headings (compress body only), list nesting, numbering, tables'
  structure, frontmatter

## Compress

Short synonyms ("big" not "extensive", "use" not "utilize"). Fragments OK
("Run tests before push", not "You should always make sure to run...").
Drop "you should"/"remember to": state the action. Merge bullets that say
the same thing. Keep one example where three show the same pattern.

## Report

`<file>: <before> -> <after> tokens (<N>% smaller). Backup: .osa/backups/.`
Then show the 3 biggest cuts so the user can veto. To undo: restore the
backup over the file.
