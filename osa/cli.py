"""Command-line entry point for the One Skill Army engine.

Subcommands:
  index [path]              build .osa/graph.json + context.md + manifest.json
  context <query> [--path]  print the smallest useful context slice
  fresh [path] [--auto]     report staleness; --auto reindexes changed files
  brief [--level]           print the always-on harness directive

Exit codes: 0 on success or fresh; 1 when `fresh` finds the index stale.
"""
import argparse

from pathlib import Path

from .analyze import explain as analyze_explain
from .analyze import shortest_path
from .brief import brief
from .context import context_slice
from .export import to_graphml, to_html
from .fresh import check
from .hook import prompt as hook_prompt
from .hook import session_start as hook_session_start
from .index import build_graph
from .measure import measure
from .store import load_graph, write_index


def _graph_for(path):
    "Return the stored graph, building it in memory if not indexed yet."
    return load_graph(path) or build_graph(path)


def _cmd_index(args):
    summary = write_index(args.path, html=not args.no_html)
    print("osa index: " + str(summary["nodes"]) + " nodes, "
          + str(summary["edges"]) + " edges written to .osa/")
    if summary["html"]:
        print("osa index: wrote " + summary["html"] + " (open in a browser)")
    return 0


def _cmd_context(args):
    graph = load_graph(args.path) or build_graph(args.path)
    print(context_slice(graph, args.query))
    return 0


def _cmd_fresh(args):
    result = check(args.path)
    if result["fresh"]:
        print("osa fresh: index up to date")
        return 0
    for label in ("added", "modified", "deleted"):
        for path in result[label]:
            print(label.upper() + " " + path)
    if args.auto:
        summary = write_index(args.path)
        print("osa fresh: reindexed (" + str(summary["nodes"]) + " nodes)")
        return 0
    if result["manifest"] is None:
        print("osa fresh: not indexed yet; run 'osa index'")
    return 1


def _cmd_brief(args):
    print(brief(level=args.level))
    return 0


def _cmd_version(args):
    from . import __version__
    print(__version__)
    return 0


def _cmd_hook(args):
    if args.event == "session-start":
        print(hook_session_start(args.path, level=args.level))
    else:
        print(hook_prompt(args.path, level=args.level))
    return 0


def _cmd_measure(args):
    r = measure(args.path)
    print("osa measure: context " + str(r["context_tokens"]) + " tokens vs "
          + "project " + str(r["project_tokens"]) + " tokens = "
          + str(r["reduction_pct"]) + "% less to get oriented ("
          + str(r["nodes"]) + " nodes, " + str(r["edges"]) + " edges)")
    return 0


def _cmd_explain(args):
    print(analyze_explain(_graph_for(args.path), args.node)["summary"])
    return 0


def _cmd_path(args):
    route = shortest_path(_graph_for(args.path), args.source, args.target)
    print(" -> ".join(route) if route else "no path between the two nodes")
    return 0


def _cmd_export(args):
    graph = _graph_for(args.path)
    osa_dir = Path(args.path) / ".osa"
    osa_dir.mkdir(parents=True, exist_ok=True)
    if args.format == "graphml":
        out = Path(args.output) if args.output else osa_dir / "graph.graphml"
        out.write_text(to_graphml(graph))
    else:
        out = Path(args.output) if args.output else osa_dir / "graph.html"
        out.write_text(to_html(graph))
    print("osa export: wrote " + str(out))
    return 0


def main(argv=None):
    "Parse arguments and dispatch to a subcommand; return an exit code."
    parser = argparse.ArgumentParser(prog="osa",
                                     description="One Skill Army engine")
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="build the project graph")
    p_index.add_argument("path", nargs="?", default=".")
    p_index.add_argument("--no-html", action="store_true",
                         help="skip writing .osa/graph.html")
    p_index.set_defaults(func=_cmd_index)

    p_context = sub.add_parser("context", help="print a context slice")
    p_context.add_argument("query")
    p_context.add_argument("--path", default=".")
    p_context.set_defaults(func=_cmd_context)

    p_fresh = sub.add_parser("fresh", help="report or refresh staleness")
    p_fresh.add_argument("path", nargs="?", default=".")
    p_fresh.add_argument("--auto", action="store_true",
                         help="reindex changed files instead of only reporting")
    p_fresh.set_defaults(func=_cmd_fresh)

    p_brief = sub.add_parser("brief", help="print the harness directive")
    p_brief.add_argument("--level", default="full",
                         choices=["lite", "full", "ultra"])
    p_brief.set_defaults(func=_cmd_brief)

    p_hook = sub.add_parser("hook", help="emit harness content for a host hook")
    p_hook.add_argument("event", choices=["session-start", "prompt"])
    p_hook.add_argument("--path", default=".")
    p_hook.add_argument("--level", default="full",
                        choices=["lite", "full", "ultra"])
    p_hook.set_defaults(func=_cmd_hook)

    p_explain = sub.add_parser("explain", help="summarize a node's role")
    p_explain.add_argument("node")
    p_explain.add_argument("--path", default=".")
    p_explain.set_defaults(func=_cmd_explain)

    p_path = sub.add_parser("path", help="shortest path between two nodes")
    p_path.add_argument("source")
    p_path.add_argument("target")
    p_path.add_argument("--path", default=".")
    p_path.set_defaults(func=_cmd_path)

    p_export = sub.add_parser("export", help="export the graph to a file")
    p_export.add_argument("format", choices=["graphml", "html"])
    p_export.add_argument("--path", default=".")
    p_export.add_argument("-o", "--output", default=None)
    p_export.set_defaults(func=_cmd_export)

    p_measure = sub.add_parser("measure",
                               help="quantify the graph's token savings")
    p_measure.add_argument("path", nargs="?", default=".")
    p_measure.set_defaults(func=_cmd_measure)

    p_version = sub.add_parser("version", help="print the pack version")
    p_version.set_defaults(func=_cmd_version)

    args = parser.parse_args(argv)
    return args.func(args)
