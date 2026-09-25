"""Content producer for the harness hooks.

Host adapters call these two functions (via `osa hook <event>`) and wrap the
returned text in whatever JSON envelope the host expects. Keeping the content
here means every host, and every model within a session, sees the same
directive: this is what makes the disciplines survive a model switch, since the
prompt event re-emits the brief on every turn.
"""
from .brief import brief
from .fresh import check
from .store import load_graph, write_index


def session_start(root=".", level="full"):
    "Refresh the index if stale, then return the brief plus a context pointer."
    status = check(root)
    if not status["fresh"]:
        # Startup stays fast: incremental, and HTML is left to `osa index`.
        write_index(root, html=False, incremental=True)
    lines = [brief(level=level)]
    if load_graph(root) is not None:
        lines.append("")
        lines.append("Project graph is built: read .osa/context.md for the map "
                     "and run 'osa context <term>' for a focused slice.")
    return "\n".join(lines)


def prompt(root=".", level="full"):
    "Return the brief to re-inject on every user prompt."
    return brief(level=level)
