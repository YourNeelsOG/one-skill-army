# Mapit: Graph Upgrade Design

Date: 2026-09-25
Status: implemented 2026-09-25 on branch `mapit-graph-upgrade`, not yet
committed. Sections 1 and 2 were approved in chat; sections 3 and 4 were
approved with "start working on coding". All 25 test files green (188
unittest methods, 304 structure checks). The graph.html side panel was not
click-tested in a real browser; rendering was verified with headless Firefox.

## Goal

Close the gap between the native `osa` engine and the external graphify tool
while keeping the engine pure Python standard library with zero external
dependencies. After this work a user can point `osa` (or `/mapit`) at any
project and get a graph that understands the common languages, labels every
edge as EXTRACTED or INFERRED, and answers plain-language questions with a
relevant subgraph.

## Decisions (made with the user, 2026-09-25)

| Question | Decision |
|---|---|
| Direction | Upgrade osa, zero dependencies. No tree-sitter, no LLM calls. |
| Languages | Core set: JS/TS (+JSX/TSX), Go, Rust, Java, SQL, shell, JSON/YAML/TOML, plus a Markdown upgrade. |
| Output dir | Stay in `.osa/`. `graphify-out/` would collide with the real graphify tool and the AGENTS.md routing rule that defers to it. |
| Naming | Skill `osa-map` and command `/osa-map` are renamed to `mapit`. The engine keeps the name `osa` (`python3 -m osa`, `osa.pyz`, `.osa/`). |
| Extractor approach | Shared comment/string scrubber plus one data table per language (approach 2 of 3). |

## Current weaknesses (verified by reading the code, 2026-09-25)

1. Only `.py` and `.md` have extractors (`osa/extractors/__init__.py`); every
   other file is a bare file node with no edges.
2. Python extraction uses `ast.walk`, which flattens scope: methods are not
   tied to their class, base classes are ignored, and calls are resolved only
   inside one file. `from . import x` is dropped because `node.module` is
   None, and `from osa.cli import x` collapses to the package `osa`.
3. Edges carry only `rel`; there is no way to tell a parsed fact from a
   heuristic match (the stem-based import resolution in `osa/index.py`).
4. `osa context` is a substring match plus direct neighbors; there is no
   question answering.
5. Markdown headings are flat and document links are not extracted.
6. `context.md` is truncated at 8000 characters and there is no full report.
   `graph.html` uses O(n^2) repulsion every frame, colors only by node kind,
   and shows no relation types or node details.
7. `osa fresh --auto` performs a full rebuild although the docs say it
   reindexes only changed files.

## Section 1: data model and edge provenance

### Edge shape

`graph.json` gains a top-level `"schema": 2`. Every edge carries a
`confidence` field:

```json
{"source": "osa/cli.py", "target": "osa/context.py", "rel": "imports",
 "confidence": "EXTRACTED", "line": 12}
```

- `EXTRACTED`: read directly from syntax (a definition, an import statement,
  a relative path resolved against the importing file, a call to a name
  defined in the same file or imported by name).
- `INFERRED`: resolved by a heuristic. Always carries a `reason` string, for
  example `"unique stem"` or `"unique name project-wide"`.
- Anything that cannot be resolved uniquely is not emitted. No third label.

A structure test asserts that every edge in a built graph has exactly one of
the two labels, and every INFERRED edge has a non-empty `reason`.

### Relation types

`defines`, `contains`, `imports`, `calls`, `inherits`, `method_of`,
`links_to`, `references`. The set is closed: extractors may emit only these,
enforced by a test.

### Python depth

- Scope-aware walk replaces `ast.walk` for definitions. Methods get ids of
  the form `path::Class.method` and a `method_of` edge to the class.
- `class A(B)` emits `inherits` A to B. B resolves through the file's own
  definitions and its imported names; otherwise it is left out.
- Relative imports resolve against the package directory to the real file
  (`EXTRACTED`). Absolute imports whose dotted path maps to a file under the
  root resolve to that file (`EXTRACTED`); the old top-level collapse is kept
  only for external packages.
- Calls: same-file calls as today (`EXTRACTED`); `from x import f` then
  `f()` resolves to `x.py::f` (`EXTRACTED`); `mod.f()` after `import mod`
  resolves the same way; a bare name unique across the project is
  `INFERRED` with reason `"unique name project-wide"`.

### Manual edges

Edges in `.osa/graph/edges.jsonl` (written by the mapit skill) are merged into
`graph.json` at index time as `INFERRED`, with the recorded evidence as the
`reason`. `osa-graph-stale.py` is otherwise unchanged this round.

## Section 2: extractors

### Scrubber

`osa/extractors/scrub.py`: `scrub(source, spec) -> str`. Replaces comment
text and string contents with spaces while preserving newlines and column
positions. Quote characters are kept so extractors can read a string literal
back from the original source at the same span. Handles line comments, block
comments, and the per-language string delimiters (including Go backticks and
JS template literals without nested `${}` parsing).

### Language tables

`osa/extractors/tables.py` holds one plain-data entry per language: file
extensions, comment syntax, string delimiters, and regex lists for
`defines` (with a node kind), `imports`, and `inherits`. One generic
`osa/extractors/table_extractor.py` runs a table over scrubbed source and
emits nodes and edges; every edge it emits is `EXTRACTED`.

| Type | Defines | Imports / references | Inherits |
|---|---|---|---|
| JS/TS/JSX/TSX | function, class, arrow const, interface, type, export | `import ... from`, `require()`, literal `import("x")` | `extends`, `implements` |
| Go | func, method, struct, interface | `import` single and grouped | struct embedding |
| Rust | fn, struct, enum, trait, impl, mod | `use`, `mod x;` | `impl Trait for X` |
| Java | class, interface, enum, record, method | `import` | `extends`, `implements` |
| SQL | table, view, function, procedure, index | FK `REFERENCES t` and view `FROM`/`JOIN t` as `references` | none |
| Shell | function | `source x` / `. x` as `imports`; repo script invocation as `references` | none |
| JSON/YAML/TOML | top-level keys as `heading` | string value naming an existing repo path as `references` (`INFERRED`); `package.json`, `Cargo.toml`, `pyproject.toml` deps as `imports` to `module` nodes | none |
| Markdown | nested headings (`contains` chain) | `[x](path)` and `@path` to a real file as `links_to` | none |

YAML and TOML are read with line regexes (TOML via `tomllib` where the
running Python has it, 3.11+); no YAML parser is added.

### Resolution

After every file is extracted, `osa/index.py` resolves import targets:

1. Relative specifiers (`./x`, `../y`, `mod x;`, `source ./a.sh`) are joined
   to the importing file's directory and matched to a real file, trying
   language extensions (JS: `.ts .tsx .js .jsx .mjs .cjs` and `/index.*`).
   Result: `EXTRACTED`.
2. A bare name equal to exactly one local file stem or directory:
   `INFERRED`, reason `"unique stem"`.
3. Otherwise the target stays an external `module` node.

### Failure handling

A file whose extractor raises stays in the graph as a bare file node (current
behavior) and its path plus the error class is recorded in the graph's
`errors` list (inside `graph.json`, one fewer file to keep in sync), surfaced
by the report.

## Section 3: query CLI (draft, needs review)

All commands accept `--path <root>` (default `.`) as today. New `--json` flag
on `query`, `explain`, `path`, `affected`, `god-nodes` prints a machine
readable result instead of text.

A shared resolver `resolve(graph, text)` maps user text to a node: exact id,
then exact name, then unique case-insensitive substring; ambiguous input
lists up to 10 candidates and exits 2.

| Command | Behavior |
|---|---|
| `osa query "<question>" [--budget N] [--depth N] [--dfs]` | Tokenize the question (split snake/camel case, drop stopwords), score nodes (exact name match > name token > path token, ties by degree), take up to 5 seeds, traverse to `--depth` (default 2, BFS; `--dfs` for depth-first), render nodes with `path:line` and edges as `a --rel [E/I]--> b`, trimmed to `--budget` tokens (default 2000, estimated with `osa/measure.py`'s `_tokens`). |
| `osa explain <node>` | Resolve, then list neighbors grouped by relation and direction with confidence, plus degree, community, and betweenness as today. |
| `osa path <a> <b>` | Resolve both, print the shortest path with each hop's relation and confidence. |
| `osa affected <node> [--depth N] [--relation R]...` | Reverse traversal over directed edges (who imports, calls, inherits, references this), default depth 2. |
| `osa god-nodes [--top N]` | Most connected nodes, default 10, external modules excluded. |
| `osa update [path] [--force] [--no-viz]` | Incremental rebuild: per-file extraction fragments are cached in `.osa/cache/fragments.json` keyed by sha256; only changed files are re-extracted, then resolution and analysis rerun over the whole graph. `--force` ignores the cache. `--no-viz` skips `graph.html`. |

Compatibility: `osa context <q>` stays unchanged. `osa fresh --auto` becomes
an alias of `osa update`. `osa index --no-viz` is accepted as an alias of
`--no-html`. The session-start hook calls the incremental update.

## Section 4: outputs (draft, needs review)

- `.osa/GRAPH_REPORT.md`, untruncated: node counts by kind; edge counts by
  relation x confidence; entrypoints; god nodes; bridges (betweenness);
  communities with an automatic label (most common directory plus the
  highest-degree member) and their top 5 members; surprising connections;
  the INFERRED edges with reasons, for human review; index errors;
  suggested questions.
- `.osa/context.md` stays the short always-read map and gains a pointer to
  `GRAPH_REPORT.md`.
- `.osa/graph.html`, still one self-contained offline file:
  color by community (toggle to kind), edge color by relation, INFERRED
  edges dashed, legend with toggles per relation and confidence, click a
  node for a side panel (`path:line`, relations grouped), search box,
  simulation that cools and stops instead of running forever, and a cheap
  grid-based repulsion instead of all pairs. Above 1500 nodes the view
  starts with symbol nodes hidden (files and modules only) and a toggle to
  show them.

## Section 5: rename osa-map to mapit

- `skills/osa-map/` becomes `skills/mapit/` (SKILL.md name field and the
  `osa-graph-stale.py` path references updated).
- `commands/osa-map.md` becomes `commands/mapit.md`. Empty argument runs
  `osa update` and reports status; subcommands `query`, `explain`, `path`,
  `affected` route to the engine.
- `scripts/pack-manifest.sh`: current lists switch to `mapit`;
  `RETIRED_SKILLS` and `RETIRED_COMMANDS` gain `osa-map` / `osa-map.md` so
  both installers prune old copies.
- References updated in: `AGENTS.md`, `README.md`, `adapters/*.md`,
  `commands/army-help.md`, `skills/memory/SKILL.md`,
  `skills/one-skill-army/SKILL.md`, `tests/test_structure.py`.

## Versioning and packaging

- Version 2.0.0 to 2.1.0 in `osa/__init__.py` and the five manifests that
  carry a version (`.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`,
  `.cursor-plugin/plugin.json`, `.zcode-plugin/plugin.json`). No test checks
  they match today; add one to `tests/test_structure.py` first.
- Rebuild `skills/one-skill-army/osa.pyz` with `python3 scripts/build-osa.py`;
  `tests/test_pyz.py` guards drift.
- README: fix the `fresh --auto` claim, document the new commands, update
  the test badge to the measured count.

## Testing

TDD per task: failing test first, watch it fail for the right reason, then
the minimum code. New test files: `test_scrub.py`, one `test_extract_<lang>.py`
per table language, `test_resolution.py`, `test_query.py`, `test_update.py`,
`test_report.py`. Each extractor test feeds a fixture snippet and asserts the
exact nodes, edges, and confidence labels, including negatives (an import in a
comment yields no edge). The existing 81 unittest methods and all structure
checks stay green. Final check: index this repo and one small mixed-language
fixture project, open `graph.html` in a browser, and confirm no console errors.

## Non-goals

- LLM or semantic extraction; PDFs, images, audio, video.
- Cross-function calls in non-Python languages.
- TypeScript path aliases from `tsconfig.json`; Go module mapping beyond a
  `go.mod` prefix match; macros; generated code.
- Type inference and dynamic import resolution.
- Graph merging across repositories, watch mode, MCP server.
- Changing the output directory or renaming the engine.

## Delivery order

Four sub-projects, each with its own plan and TDD cycle, merged in order:
A (Section 1 plus Section 5 rename), B (Section 2), C (Section 3),
D (Section 4).
