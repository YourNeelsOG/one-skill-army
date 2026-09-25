"""Structural extractor for JSON, YAML and TOML config files.

Top-level keys become `heading` nodes so config sections are navigable.
Dependency manifests (package.json, Cargo.toml, pyproject.toml) emit imports
edges to external `module` nodes, which is a fact stated in the file. Any path
written in the file (`scripts/build.sh`, `./src/app.ts`) becomes a pending
references edge matched by path suffix, so it is INFERRED. Lock files only get
a file node: they are machine-written and would flood the graph.

JSON and TOML (Python 3.11+ `tomllib`) are parsed properly. YAML has no
stdlib parser, so its keys are read with a column-0 regex after comments are
scrubbed.
"""
import json
import posixpath
import re

from .scrub import scrub
from .tables import path_suffixes

try:
    import tomllib
except ImportError:  # Python < 3.11: TOML falls back to regex headings only
    tomllib = None

# A path with at least one "/" and an extension. The lookbehind rejects a
# start inside a URL or a longer path, so https://x/a.sh never matches.
PATH_TOKEN = re.compile(
    r"(?<![\w/.:@$-])((?:\.{1,2}/)?[\w.-]+(?:/[\w.-]+)+\.[A-Za-z]\w*)\b")
YAML_KEY = re.compile(r"^([A-Za-z_][\w.-]*)\s*:", re.MULTILINE)
TOML_TABLE = re.compile(r"^\[+\s*([\w.-]+)", re.MULTILINE)
TOML_KEY = re.compile(r"^([A-Za-z_][\w-]*)\s*=", re.MULTILINE)
PEP508_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")

NPM_DEP_KEYS = ("dependencies", "devDependencies", "peerDependencies",
                "optionalDependencies")
CARGO_DEP_KEYS = ("dependencies", "dev-dependencies", "build-dependencies")


def _line_of(text, needle):
    "Line of the first occurrence of needle, 1 if absent."
    idx = text.find(needle)
    return text.count("\n", 0, idx) + 1 if idx >= 0 else 1


def _dependencies(name, data):
    "Return external package names declared by a known manifest."
    if not isinstance(data, dict):
        return []
    out = []
    if name == "package.json":
        for key in NPM_DEP_KEYS:
            if isinstance(data.get(key), dict):
                out.extend(data[key])
    elif name == "Cargo.toml":
        for key in CARGO_DEP_KEYS:
            if isinstance(data.get(key), dict):
                out.extend(data[key])
    elif name == "pyproject.toml":
        project = data.get("project", {})
        specs = list(project.get("dependencies", []))
        for group in project.get("optional-dependencies", {}).values():
            specs.extend(group)
        for spec in specs:
            m = PEP508_NAME.match(str(spec))
            if m:
                out.append(m.group(1))
        poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        out.extend(k for k in poetry if k != "python")
    return out


def extract(path, source):
    "Return file node, top-level key nodes, dependency and path edges."
    name = posixpath.basename(path)
    ext = posixpath.splitext(name)[1].lower()
    lang = {".json": "json", ".toml": "toml"}.get(ext, "yaml")
    nodes = [{"id": path, "kind": "file", "name": path, "path": path,
              "line": 1, "lang": lang}]
    edges = []
    if "lock" in name.lower():
        return {"nodes": nodes, "edges": edges}

    data, keys = None, []
    text = source
    if lang == "json":
        try:
            data = json.loads(source)
        except ValueError:
            return {"nodes": nodes, "edges": edges}
        keys = list(data) if isinstance(data, dict) else []
    elif lang == "toml":
        text = scrub(source, line=["#"], strings=['"', "'"])
        if tomllib is not None:
            try:
                data = tomllib.loads(source)
                keys = list(data)
            except tomllib.TOMLDecodeError:
                data = None
        if data is None:
            keys = [m.group(1).split(".")[0] for m in TOML_TABLE.finditer(text)]
            keys += [m.group(1) for m in TOML_KEY.finditer(text)]
        # TOML strings hold the paths; keep them, only comments go.
        text = scrub(source, line=["#"])
    else:
        text = scrub(source, line=["#"])
        keys = [m.group(1) for m in YAML_KEY.finditer(text)]

    seen = set()
    for key in keys:
        hid = path + "#" + str(key)
        if hid in seen:
            continue
        seen.add(hid)
        nodes.append({"id": hid, "kind": "heading", "name": str(key),
                      "path": path, "line": _line_of(source, str(key)),
                      "lang": lang})
        edges.append({"source": path, "target": hid, "rel": "contains",
                      "confidence": "EXTRACTED"})

    for dep in _dependencies(name, data):
        edges.append({"source": path, "rel": "imports",
                      "line": _line_of(source, dep),
                      "resolve": {"module": dep}})

    for m in PATH_TOKEN.finditer(text):
        spec = path_suffixes(path, m.group(1))
        if spec:
            edges.append({"source": path, "rel": "references",
                          "line": text.count("\n", 0, m.start()) + 1,
                          "resolve": spec})
    return {"nodes": nodes, "edges": edges}
