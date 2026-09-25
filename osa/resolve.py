"""Turn pending edges into real edges once every file has been extracted.

An extractor sees one file, so it cannot know whether `import util` means a
local file or an external package. It emits a pending edge instead: a normal
edge whose `target` is missing and whose `resolve` dict lists what to try:

- `files`:  candidate file paths, in order. The first one that exists wins.
- `symbol`: with `files`, the edge points at `<file>::<symbol>`, not the file.
- `module`: import fallback. External package id when nothing local matches.
- `stem`:   import fallback. A name that may equal exactly one local file stem.
- `name`:   bare-name fallback. A name that may equal exactly one top-level
            symbol in the whole project.
- `langs`:  with `name`, only symbols in these languages count, so a Python
            `User` never resolves to a TypeScript `User`.

Resolution order and confidence:
1. A candidate file (and symbol) that exists: EXTRACTED. The path follows from
   the syntax alone.
2. A stem matching exactly one local file: INFERRED, reason "unique stem".
3. `module` given and nothing local matched: external module node, EXTRACTED
   (importing an external package is a fact in the source).
4. A bare name matching exactly one top-level symbol: INFERRED, reason
   "unique name project-wide".
5. Anything else is dropped. The engine never guesses between candidates.
"""
from collections import Counter, defaultdict
from pathlib import PurePosixPath
from types import SimpleNamespace


def _indexes(nodes):
    """Build the lookup tables resolution needs from the merged node dict.

    Everything is keyed so one pending edge costs a few dict lookups, not a
    scan of every file: suffix matches go through the file's basename, and
    package directories are grouped by file extension on first use.
    """
    files = {nid for nid, n in nodes.items() if n.get("kind") == "file"}
    stems = Counter(PurePosixPath(f).stem for f in files)
    by_basename = defaultdict(list)
    for f in files:
        by_basename[PurePosixPath(f).name].append(f)
    # Top-level symbols only: "path::name" with no dot in the name part, so a
    # method named like a function never makes a bare call look ambiguous.
    by_name = defaultdict(list)
    for nid, n in nodes.items():
        if "::" in nid and "." not in nid.split("::", 1)[1]:
            by_name[n.get("name")].append(nid)
    return SimpleNamespace(
        files=files,
        stem_to_file={PurePosixPath(f).stem: f for f in files
                      if stems[PurePosixPath(f).stem] == 1},
        by_basename=by_basename, by_name=by_name, dirs_by_ext={})


def _package_dirs(idx, ext):
    "Directories holding at least one file with this extension (cached)."
    if ext not in idx.dirs_by_ext:
        idx.dirs_by_ext[ext] = {PurePosixPath(f).parent.as_posix()
                                for f in idx.files if f.endswith(ext)} - {"."}
    return idx.dirs_by_ext[ext]


def _resolve_one(edge, spec, nodes, idx):
    "Return (target, confidence, reason) for one pending edge, or None."
    symbol = spec.get("symbol")
    for cand in spec.get("files") or ():
        if cand not in idx.files:
            continue
        target = cand + "::" + symbol if symbol else cand
        if target in nodes:
            return target, "EXTRACTED", None
    for suffix in spec.get("suffixes") or ():
        hits = [f for f in idx.by_basename.get(PurePosixPath(suffix).name, ())
                if f == suffix or f.endswith("/" + suffix)]
        if len(hits) == 1 and hits[0] != edge["source"]:
            return hits[0], "INFERRED", "path suffix"
        if hits:
            break  # ambiguous here means ambiguous for every shorter suffix
    package = spec.get("package")
    if package:
        # The longest trailing run of path segments that is a local package
        # directory wins: internal/store beats store.
        dirs = _package_dirs(idx, spec.get("package_ext", ""))
        segs = package.split("/")
        for k in range(len(segs)):
            cand = "/".join(segs[k:])
            if cand in dirs:
                return cand + "/", "INFERRED", "path suffix"
    stem = spec.get("stem")
    hit = idx.stem_to_file.get(stem) if stem else None
    if hit and hit != edge["source"]:
        return hit, "INFERRED", "unique stem"
    module = spec.get("module")
    if module:
        return module, "EXTRACTED", None
    name = spec.get("name")
    if name:
        langs = spec.get("langs")
        found = [nid for nid in idx.by_name.get(name, ())
                 if not langs or nodes[nid].get("lang") in langs]
        if len(found) == 1 and found[0] != edge["source"]:
            return found[0], "INFERRED", "unique name project-wide"
    return None


def _package_node(nodes, pkg_id, spec):
    "Create a directory package node; return contains edges to its files."
    directory = pkg_id.rstrip("/")
    ext = spec.get("package_ext", "")
    members = sorted(nid for nid, n in nodes.items()
                     if n.get("kind") == "file" and nid.endswith(ext)
                     and PurePosixPath(nid).parent.as_posix() == directory)
    nodes[pkg_id] = {"id": pkg_id, "kind": "package", "name": directory,
                     "path": directory, "line": 1,
                     "lang": nodes[members[0]].get("lang", "generic")}
    return [{"source": pkg_id, "target": m, "rel": "contains",
             "confidence": "EXTRACTED"} for m in members]


def resolve_edges(nodes, edges):
    """Resolve pending edges in place of `edges`; return the final edge list.

    `nodes` is the merged {id: node} dict and gains a module node for each
    external package an import resolves to, and a package node (id ending in
    "/") for each local Go-style directory package. Final edges are de-duplicated
    by (source, target, rel); an EXTRACTED copy beats an INFERRED one.
    """
    idx = _indexes(nodes)
    out = {}
    extra = []  # contains edges for package nodes created during resolution
    for edge in edges:
        spec = edge.get("resolve")
        if spec is not None:
            hit = _resolve_one(edge, spec, nodes, idx)
            if hit is None:
                continue
            target, confidence, reason = hit
            edge = {k: v for k, v in edge.items() if k != "resolve"}
            edge["target"] = target
            edge["confidence"] = confidence
            if reason:
                edge["reason"] = reason
            if target not in nodes and target.endswith("/"):
                extra.extend(_package_node(nodes, target, spec))
            elif target not in nodes:
                nodes[target] = {"id": target, "kind": "module",
                                 "name": target, "path": edge["source"],
                                 "line": edge.get("line", 1),
                                 "lang": nodes.get(edge["source"], {})
                                 .get("lang", "generic")}
        key = (edge["source"], edge["target"], edge["rel"])
        old = out.get(key)
        if old is None or (old["confidence"] == "INFERRED"
                           and edge["confidence"] == "EXTRACTED"):
            out[key] = edge
    for edge in extra:
        out.setdefault((edge["source"], edge["target"], edge["rel"]), edge)
    # A path that is imported (a sourced script) is not also a reference.
    for (source, target, rel) in list(out):
        if rel == "references" and (source, target, "imports") in out:
            del out[(source, target, rel)]
    return list(out.values())
