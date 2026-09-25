"""Extractor registry: dispatch a file to the right structural parser.

Maps a file extension to an extractor module or a language table. Every
extractor returns `{"nodes": [...], "edges": [...]}` for one file. Files with no
registered extension fall back to the generic extractor, which still emits a
file node so nothing disappears from the graph.
"""
from pathlib import Path

from . import config, generic, markdown, python_ast
from .table_extractor import extract_with
from .tables import TABLES

# Extension (lowercase, with dot) -> extractor module.
_REGISTRY = {
    ".py": python_ast,
    ".md": markdown,
    ".markdown": markdown,
    ".json": config,
    ".yaml": config,
    ".yml": config,
    ".toml": config,
}
# Extension -> language table for the shared regex engine.
_TABLES = {ext: table for table in TABLES for ext in table["ext"]}


def extract_file(path, source):
    "Dispatch one file to its extractor, falling back to generic."
    ext = Path(path).suffix.lower()
    if ext in _TABLES:
        return extract_with(_TABLES[ext], path, source)
    extractor = _REGISTRY.get(ext, generic)
    return extractor.extract(path, source)
