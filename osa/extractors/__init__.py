"""Extractor registry: dispatch a file to the right structural parser.

Maps a file extension to an extractor module. Every extractor exposes
`extract(path, source) -> {"nodes": [...], "edges": [...]}`. Files with no
registered extension fall back to the generic extractor, which still emits a
file node so nothing disappears from the graph.
"""
from pathlib import Path

from . import generic, markdown, python_ast

# Extension (lowercase, with dot) -> extractor module.
_REGISTRY = {
    ".py": python_ast,
    ".md": markdown,
    ".markdown": markdown,
}


def extract_file(path, source):
    "Dispatch one file to its extractor, falling back to generic."
    ext = Path(path).suffix.lower()
    extractor = _REGISTRY.get(ext, generic)
    return extractor.extract(path, source)
