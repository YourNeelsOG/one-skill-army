# Mapit Graph Upgrade: Implementation Plan

Spec: `docs/specs/2026-09-25-mapit-graph-upgrade-design.md`. Every task is
TDD: failing test first, then minimum code. Suite command:
`for f in tests/test_*.py; do python3 "$f" || echo "FAIL $f"; done`.

## A: provenance, Python depth, rename

1. `tests/test_provenance.py`: every edge from `build_graph` has
   `confidence` in {EXTRACTED, INFERRED}; INFERRED has `reason`; `rel` in the
   closed set; graph has `schema: 2`. Update exact-dict assertions in
   `test_python_extractor.py` and `test_index.py` to the new edge shape.
2. Pending-edge contract: extractors may emit an edge with a `resolve` dict
   (`files`, `symbol`, `module`, `name`) instead of a final `target`;
   `osa/resolve.py` turns it into a real edge or drops it. Replaces
   `_resolve_internal_imports` in `osa/index.py`. Edges deduped by
   (source, target, rel).
3. Python: scope-aware definitions (`Class.method`, `method_of`), `inherits`,
   relative and absolute imports to files, cross-file calls through imported
   names, unique-name INFERRED calls (builtins excluded).
4. Manual edges from `.osa/graph/edges.jsonl` merged as INFERRED with
   evidence as reason, `origin: manual`.
5. Rename skill and command `osa-map` to `mapit`; retire old names in
   `scripts/pack-manifest.sh`; update references; structure tests first.
6. Version sync test, then bump to 2.1.0.

## B: extractors

7. `osa/extractors/scrub.py` + `tests/test_scrub.py`.
8. `tables.py` + `table_extractor.py`, one language at a time with its own
   test file: JS/TS, Go, Rust, Java, SQL, shell.
9. Config extractor (JSON/YAML/TOML) and Markdown upgrade (nested headings,
   `links_to`).
10. Index errors recorded in `graph.json` under `errors`.

## C: query CLI

11. `osa/query.py`: `resolve_node`, `query`, `affected`; tests first.
12. CLI: `query`, `affected`, `god-nodes`, `update`, `--json`, richer
    `explain` and `path`, `--no-viz` alias, `fresh --auto` routes to update.
13. Fragment cache for incremental `update`; hook uses it.

## D: outputs

14. `osa/report.py` writes `.osa/GRAPH_REPORT.md`; `context.md` points to it.
15. `graph.html` rewrite: community colors, relation colors, dashed
    INFERRED, legend toggles, side panel, cooling, grid repulsion.
16. Rebuild `osa.pyz`, README and docs, final full-suite and browser check.
