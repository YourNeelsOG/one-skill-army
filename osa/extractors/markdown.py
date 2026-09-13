"""Structural extractor for Markdown documents.

Treats ATX headings (lines beginning with one or more '#') as the document's
structure. Each heading becomes a node and the file gets a contains edge to it,
so docs are navigable in the same graph as code.
"""
import re

HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def extract(path, source):
    "Return the file node plus one heading node per ATX heading."
    nodes = [{"id": path, "kind": "file", "name": path, "path": path,
              "line": 1, "lang": "markdown"}]
    edges = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        m = HEADING.match(line)
        if not m:
            continue
        title = m.group(2).strip()
        hid = path + "#" + title
        nodes.append({"id": hid, "kind": "heading", "name": title,
                      "path": path, "line": lineno, "lang": "markdown"})
        edges.append({"source": path, "target": hid, "rel": "contains"})
    return {"nodes": nodes, "edges": edges}
