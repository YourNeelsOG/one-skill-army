"""Persist and load the project graph and its derived artifacts.

`write_index` is the whole `osa index` pipeline: build the graph, render the
context digest, and write all three files plus the freshness manifest under
.osa/. `load_graph` reads the stored graph back for `osa context` and `osa
fresh` without rebuilding it.
"""
import json
from pathlib import Path

from .context import build_context
from .export import to_html
from .fresh import write_manifest
from .index import build_graph


def _osa_dir(root):
    return Path(root) / ".osa"


def write_index(root, html=True):
    "Build the graph and write graph.json, context.md, manifest.json, graph.html."
    graph = build_graph(root)
    out = _osa_dir(root)
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph.json").write_text(json.dumps(graph, indent=2, sort_keys=True))
    # The persisted map is read once per session; give it a generous budget so
    # the analysis sections survive (the query slice stays tight elsewhere).
    (out / "context.md").write_text(build_context(graph, budget=8000))
    write_manifest(root)
    summary = {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
               "html": None}
    if html:
        html_path = out / "graph.html"
        html_path.write_text(to_html(graph))
        summary["html"] = str(html_path)
    return summary


def load_graph(root):
    "Return the stored graph, or None when the project has not been indexed."
    gp = _osa_dir(root) / "graph.json"
    if not gp.is_file():
        return None
    try:
        return json.loads(gp.read_text())
    except (OSError, ValueError):
        return None
