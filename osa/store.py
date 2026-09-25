"""Persist and load the project graph and its derived artifacts.

`write_index` is the whole `osa index` / `osa update` pipeline: build the
graph, render the context digest and the full report, and write them plus the
HTML view, the fragment cache, and the freshness manifest under .osa/. `load_graph` reads the stored graph back for `osa context` and `osa
fresh` without rebuilding it.
"""
import json
from pathlib import Path

from .context import build_context
from .export import to_html
from .fresh import write_manifest
from .index import build_graph
from .report import build_report


def _osa_dir(root):
    return Path(root) / ".osa"


def _load_cache(path):
    "Return the fragment cache, or {} when missing or unreadable."
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_index(root, html=True, incremental=False):
    """Build the graph and write graph.json, context.md, manifest, graph.html.

    incremental=True reuses cached per-file fragments for unchanged files
    (.osa/cache/fragments.json); the cache is rewritten on every run so the
    next incremental run has a baseline.
    """
    out = _osa_dir(root)
    cache_path = out / "cache" / "fragments.json"
    cache = _load_cache(cache_path) if incremental else {}
    previous = {rel: entry.get("sha256") for rel, entry in cache.items()
                if isinstance(entry, dict)}
    graph = build_graph(root, cache=cache)
    out.mkdir(parents=True, exist_ok=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache))
    (out / "graph.json").write_text(json.dumps(graph, indent=2, sort_keys=True))
    # The persisted map is read once per session; give it a generous budget so
    # the analysis sections survive (the query slice stays tight elsewhere).
    (out / "context.md").write_text(build_context(graph, budget=8000))
    (out / "GRAPH_REPORT.md").write_text(build_report(graph))
    write_manifest(root)
    extracted = sum(1 for rel, entry in cache.items()
                    if previous.get(rel) != entry["sha256"])
    summary = {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
               "extracted": extracted, "html": None}
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
