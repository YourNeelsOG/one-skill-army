---
description: "Set One Skill Army intensity: lite | full | ultra | off. Affects prose compression and ladder strictness."
argument-hint: "[lite|full|ultra|off]"
---

Set the pack intensity.

User's requested level: $ARGUMENTS

Valid levels, exactly: `lite`, `full` (default), `ultra`, `off`. Nothing
else is a level. If $ARGUMENTS is empty, or is not one of these four words
("high", "max", "medium", and numbers are NOT levels), do NOT map it to the
closest level and do NOT set anything: list the four levels in one line and
ask the user to pick. Never guess.

- `lite`: no filler/hedging, keep full sentences. Build what's asked, name
  the lazier alternative in one line.
- `full`: articles dropped, fragments OK, short synonyms. Ladder enforced:
  stdlib and native first, shortest diff. Default.
- `ultra`: telegram style, facts intact. YAGNI extremist: deletion before
  addition, ship the one-liner and challenge the rest of the requirement.
- `off`: normal prose, normal build style.

Never changed by this command: anti-hallucination, verification,
code-commenting, git-safety. Those have no intensity dial.

Confirm the new level in one line. No announcement theater.
