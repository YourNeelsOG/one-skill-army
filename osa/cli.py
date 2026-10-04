"""Command-line entry point for the One Skill Army engine.

Subcommands (run `osa <command> -h` for options):
  install [path]            install project skills and automatic routing
  lessons harvest|due       digest recent chats for lessons.md, or check if due
  doctor [path]             verify the project installation
  index [path]              full build: .osa/graph.json, context.md, graph.html
  update [path]             incremental build: re-parse only changed files
  query "<question>"        relevant subgraph for a plain-language question
  explain <node>            a node's relations, grouped, with EXTRACTED/INFERRED
  path <a> <b>              shortest path with the relation of every hop
  affected <node>           what depends on a node (reverse traversal)
  god-nodes                 most connected nodes
  context <query>           substring slice (kept for older hooks and docs)
  fresh [path] [--auto]     report staleness; --auto runs `update`
  brief [--level]           print the always-on harness directive

Exit codes: 0 on success or fresh; 1 when `fresh` finds the index stale or a
node is not found; 2 when a node name is ambiguous (candidates are printed).
"""
import argparse
import sys
import json

from pathlib import Path

from .analyze import betweenness, communities
from .analyze import shortest_path
from .brief import brief
from .context import context_slice
from .export import to_graphml, to_html
from .fresh import check
from .hook import prompt as hook_prompt
from .hook import session_start as hook_session_start
from .graph import degree
from .index import build_graph
from .measure import measure
from .query import affected, describe, path_hops, query, resolve_node
from .store import load_graph, write_index


def _graph_for(path):
    "Return the stored graph, building it in memory if not indexed yet."
    return load_graph(path) or build_graph(path)


def _emit(args, data, text):
    "Print JSON when --json was given, otherwise the human text."
    print(json.dumps(data, indent=2) if getattr(args, "json", False)
          else text)


def _resolve_or_report(graph, text):
    "Return (node_id, exit_code); prints candidates or 'not found' on failure."
    node, candidates = resolve_node(graph, text)
    if node:
        return node, 0
    if candidates:
        print("ambiguous '" + text + "', did you mean:")
        for cand in candidates:
            print("  " + cand)
        return None, 2
    print("no node matches '" + text + "'")
    return None, 1


def _report_build(label, summary):
    print("osa " + label + ": " + str(summary["nodes"]) + " nodes, "
          + str(summary["edges"]) + " edges written to .osa/ ("
          + str(summary["extracted"]) + " re-extracted)")
    if summary["html"]:
        print("osa " + label + ": wrote " + summary["html"]
              + " (open in a browser)")


def _cmd_index(args):
    _report_build("index", write_index(args.path, html=not args.no_html))
    return 0


def _cmd_update(args):
    summary = write_index(args.path, html=not args.no_html,
                          incremental=not args.force)
    _report_build("update", summary)
    return 0


def _cmd_query(args):
    result = query(_graph_for(args.path), args.question, depth=args.depth,
                   budget=args.budget, dfs=args.dfs)
    _emit(args, {k: result[k] for k in ("seeds", "nodes", "edges")},
          result["text"])
    return 0


def _cmd_affected(args):
    graph = _graph_for(args.path)
    node, code = _resolve_or_report(graph, args.node)
    if not node:
        return code
    hits = affected(graph, node, depth=args.depth, relations=args.relation)
    lines = ["Affected by " + node + " (depth " + str(args.depth) + "):"]
    lines += ["  " + str(h["depth"]) + "  " + h["id"] + "  (" + h["rel"]
              + ")" for h in hits] or ["  nothing depends on it"]
    _emit(args, hits, "\n".join(lines))
    return 0


def _cmd_god_nodes(args):
    graph = _graph_for(args.path)
    deg = degree(graph)
    kinds = {n["id"]: n.get("kind") for n in graph["nodes"]}
    ranked = sorted((nid for nid in deg if kinds.get(nid) != "module"),
                    key=lambda nid: (-deg[nid], nid))[:args.top]
    rows = [{"id": nid, "degree": deg[nid], "kind": kinds[nid]}
            for nid in ranked]
    _emit(args, rows, "\n".join(str(r["degree"]).rjust(5) + "  " + r["id"]
                                + " (" + str(r["kind"]) + ")" for r in rows))
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
        summary = write_index(args.path, incremental=True)
        print("osa fresh: reindexed (" + str(summary["nodes"]) + " nodes, "
              + str(summary["extracted"]) + " re-extracted)")
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


def _cmd_install(args):
    "Install project-owned resources and report boundary failures clearly."
    from .install import install_project
    try:
        receipt = install_project(args.path, Path(__file__).resolve().parent.parent,
                                  hosts=args.hosts, level=args.level)
    except (OSError, ValueError) as error:
        print("osa install: " + str(error))
        return 1
    print("osa install: " + str(receipt["skill_count"]) + " skills installed in "
          + str(Path(args.path).resolve()))
    print("Automatic poteto routing active; token optimization: " + receipt["level"]
          + ". Start a new host session. No model setup is required.")
    return 0


def _cmd_doctor(args):
    "Check the installed payload and discovery entries without mutating them."
    from .install import doctor_project
    try:
        result = doctor_project(args.path)
    except (OSError, ValueError) as error:
        print("osa doctor: " + str(error))
        return 1
    if result["ok"]:
        print("osa doctor: project installation is complete.")
        return 0
    for issue in result["issues"]:
        print("osa doctor: " + issue)
    return 1


def _cmd_lessons(args):
    "Print a harvest digest and record it, or report whether one is due."
    from . import lessons
    if args.action == "harvest":
        print(lessons.render(lessons.harvest(hours=args.hours), budget=args.budget), end="")
        try:
            lessons.mark()
        except OSError as error:
            # The digest is still useful; only the automatic interval is lost.
            print("osa lessons: could not record harvest time: " + str(error), file=sys.stderr)
        return 0
    if lessons.due(hours=args.hours):
        print("Lessons harvest due: run update-lesson at the end of this task.")
        return 0
    print("Lessons harvest not due.")
    return 1


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
    graph = _graph_for(args.path)
    node, code = _resolve_or_report(graph, args.node)
    if not node:
        return code
    info = describe(graph, node)
    comm = communities(graph).get(node)
    info["community"] = comm
    info["betweenness"] = round(betweenness(graph).get(node, 0.0), 2)
    text = (info["text"] + "\n  community " + str(comm) + ", betweenness "
            + str(info["betweenness"]))
    _emit(args, {k: v for k, v in info.items() if k != "text"}, text)
    return 0


def _cmd_path(args):
    graph = _graph_for(args.path)
    ends = []
    for text in (args.source, args.target):
        node, code = _resolve_or_report(graph, text)
        if not node:
            return code
        ends.append(node)
    route = shortest_path(graph, ends[0], ends[1])
    hops = path_hops(graph, route)
    if not route:
        text = "no path between " + ends[0] + " and " + ends[1]
    else:
        lines = [route[0]]
        for hop in hops:
            tag = "[E]" if hop["confidence"] == "EXTRACTED" else "[I]"
            arrow = ("--" + hop["rel"] + " " + tag + "-->"
                     if hop["direction"] == "->"
                     else "<--" + hop["rel"] + " " + tag + "--")
            lines.append("  " + arrow + " " + hop["target"])
        text = "\n".join(lines)
    _emit(args, {"route": route, "hops": hops}, text)
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

    p_install = sub.add_parser("install", help="install OSA into a project")
    p_install.add_argument("path", nargs="?", default=".")
    p_install.add_argument("--hosts", nargs="+", default=["codex", "claude", "grok", "zcode"],
                           choices=["codex", "claude", "grok", "zcode"])
    p_install.add_argument("--level", choices=["lite", "full", "ultra", "off"], default=None,
                           help="override the project's token optimization level")
    p_install.set_defaults(func=_cmd_install)

    p_doctor = sub.add_parser("doctor", help="verify an OSA project installation")
    p_doctor.add_argument("path", nargs="?", default=".")
    p_doctor.set_defaults(func=_cmd_doctor)

    p_index = sub.add_parser("index", help="build the project graph")
    p_index.add_argument("path", nargs="?", default=".")
    p_index.add_argument("--no-html", "--no-viz", dest="no_html",
                         action="store_true",
                         help="skip writing .osa/graph.html")
    p_index.set_defaults(func=_cmd_index)

    p_update = sub.add_parser("update",
                              help="incremental rebuild of changed files")
    p_update.add_argument("path", nargs="?", default=".")
    p_update.add_argument("--force", action="store_true",
                          help="ignore the cache and re-parse every file")
    p_update.add_argument("--no-viz", "--no-html", dest="no_html",
                          action="store_true",
                          help="skip writing .osa/graph.html")
    p_update.set_defaults(func=_cmd_update)

    p_query = sub.add_parser("query", help="answer a question with a subgraph")
    p_query.add_argument("question")
    p_query.add_argument("--path", default=".")
    p_query.add_argument("--depth", type=int, default=2,
                         help="hops out from the best matches (default 2)")
    p_query.add_argument("--budget", type=int, default=2000,
                         help="cap output at N tokens (default 2000)")
    p_query.add_argument("--dfs", action="store_true",
                         help="depth-first instead of breadth-first")
    p_query.add_argument("--json", action="store_true")
    p_query.set_defaults(func=_cmd_query)

    p_aff = sub.add_parser("affected", help="what depends on a node")
    p_aff.add_argument("node")
    p_aff.add_argument("--path", default=".")
    p_aff.add_argument("--depth", type=int, default=2)
    p_aff.add_argument("--relation", action="append", default=None,
                       help="only follow this relation (repeatable)")
    p_aff.add_argument("--json", action="store_true")
    p_aff.set_defaults(func=_cmd_affected)

    p_god = sub.add_parser("god-nodes", help="most connected nodes")
    p_god.add_argument("--path", default=".")
    p_god.add_argument("--top", type=int, default=10)
    p_god.add_argument("--json", action="store_true")
    p_god.set_defaults(func=_cmd_god_nodes)

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
    p_brief.add_argument("--level", default="ultra",
                         choices=["lite", "full", "ultra"])
    p_brief.set_defaults(func=_cmd_brief)

    p_hook = sub.add_parser("hook", help="emit harness content for a host hook")
    p_hook.add_argument("event", choices=["session-start", "prompt"])
    p_hook.add_argument("--path", default=".")
    p_hook.add_argument("--level", default="ultra",
                        choices=["lite", "full", "ultra"])
    p_hook.set_defaults(func=_cmd_hook)

    p_explain = sub.add_parser("explain", help="a node's relations and role")
    p_explain.add_argument("node")
    p_explain.add_argument("--path", default=".")
    p_explain.add_argument("--json", action="store_true")
    p_explain.set_defaults(func=_cmd_explain)

    p_path = sub.add_parser("path", help="shortest path between two nodes")
    p_path.add_argument("source")
    p_path.add_argument("target")
    p_path.add_argument("--path", default=".")
    p_path.add_argument("--json", action="store_true")
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

    p_lessons = sub.add_parser("lessons", help="harvest chats for lessons.md, or check if due")
    p_lessons.add_argument("action", choices=["harvest", "due"])
    p_lessons.add_argument("--hours", type=float, default=None,
                           help="harvest window (default 48) or due interval (default 24)")
    p_lessons.add_argument("--budget", type=int, default=12000, help="max digest characters")
    p_lessons.set_defaults(func=_cmd_lessons)

    p_version = sub.add_parser("version", help="print the pack version")
    p_version.set_defaults(func=_cmd_version)

    args = parser.parse_args(argv)
    if args.command == "lessons" and args.hours is None:
        args.hours = 48 if args.action == "harvest" else 24
    return args.func(args)
