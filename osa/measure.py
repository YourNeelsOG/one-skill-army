"""Quantify what the graph saves: measured, not claimed.

The value of the prebuilt graph is that an agent reads a small map instead of
scanning the whole repository to get oriented. This reports that concretely:
how many tokens the context digest costs versus how many the raw project costs,
and the reduction between them. Token counts are estimated at 4 characters per
token, the usual rough rule; the ratio is what matters, not the absolute count.
"""
from .context import build_context
from .index import build_graph
from .scan import scan

CHARS_PER_TOKEN = 4


def _tokens(text):
    return max(1, len(text) // CHARS_PER_TOKEN)


def measure(root):
    "Return token counts for the context map vs the whole project, and savings."
    project_chars = 0
    for _rel, path in scan(root):
        try:
            project_chars += len(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    graph = build_graph(root)
    context = build_context(graph, budget=8000)

    project_tokens = max(1, project_chars // CHARS_PER_TOKEN)
    context_tokens = _tokens(context)
    reduction = 100.0 * (project_tokens - context_tokens) / project_tokens
    reduction = max(0.0, min(100.0, reduction))
    return {
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "context_tokens": context_tokens,
        "project_tokens": project_tokens,
        "reduction_pct": round(reduction, 1),
    }
