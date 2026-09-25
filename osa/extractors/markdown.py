"""Structural extractor for Markdown documents.

ATX headings (lines starting with '#') become heading nodes nested by level: a
`##` under a `#` hangs off that heading, so a document reads as a tree. Links
to local files (`[text](docs/x.md)`) and `@path` mentions (as in CLAUDE.md's
`@AGENTS.md`) become pending links_to edges that resolve only when the file
exists. Fenced code blocks and inline code are skipped, so examples in docs
never create headings or links.
"""
import posixpath
import re

HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
MENTION = re.compile(r"(?:^|(?<=\s))@([\w./-]+\.\w+)")


def _link_target(path, raw):
    "Candidate file for a link, or None for URLs, anchors and escapes."
    if "://" in raw or raw.startswith(("mailto:", "#", "tel:")):
        return None
    raw = raw.split("#", 1)[0].split("?", 1)[0]
    if not raw:
        return None
    if raw.startswith("/"):
        joined = posixpath.normpath(raw.lstrip("/"))
    else:
        joined = posixpath.normpath(posixpath.join(posixpath.dirname(path),
                                                   raw))
    return None if joined.startswith("..") else joined


def extract(path, source):
    "Return the file node, nested heading nodes, and pending link edges."
    nodes = [{"id": path, "kind": "file", "name": path, "path": path,
              "line": 1, "lang": "markdown"}]
    edges = []
    parents = []  # stack of (level, heading id)
    in_fence = False
    for lineno, line in enumerate(source.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            hid = path + "#" + title
            while parents and parents[-1][0] >= level:
                parents.pop()
            parent = parents[-1][1] if parents else path
            nodes.append({"id": hid, "kind": "heading", "name": title,
                          "path": path, "line": lineno, "lang": "markdown"})
            edges.append({"source": parent, "target": hid, "rel": "contains",
                          "confidence": "EXTRACTED"})
            parents.append((level, hid))
            continue
        text = INLINE_CODE.sub(lambda c: " " * len(c.group(0)), line)
        for pattern in (LINK, MENTION):
            for lm in pattern.finditer(text):
                target = _link_target(path, lm.group(1))
                if target and target != path:
                    edges.append({"source": path, "rel": "links_to",
                                  "line": lineno,
                                  "resolve": {"files": [target]}})
    return {"nodes": nodes, "edges": edges}
