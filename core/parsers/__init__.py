# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
"""
Parser plugin system for impact-engine.

To add a new language parser:
  1. Create a subclass of BaseParser in core/parsers/
  2. Register it with the @register_parser decorator
  3. The parser is auto-discovered and used for matching file extensions

Example:
    @register_parser(".rs", ".rlib")
    class RustParser(BaseParser):
        def extract_dependencies(self, file_path: str, base_dir: str) -> Dict[str, List[str]]:
            ...
"""
import importlib
import os
import pkgutil
from typing import Dict, List, Optional, Type

_PARSER_REGISTRY: Dict[str, Type["BaseParser"]] = {}
_DISCOVERED = False


def _discover_parsers():
    global _DISCOVERED
    if _DISCOVERED:
        return
    _DISCOVERED = True
    pkg_dir = os.path.dirname(__file__)
    for _, name, _ in pkgutil.iter_modules([pkg_dir]):
        if name != "__init__":
            importlib.import_module(f"core.parsers.{name}")


def register_parser(*extensions: str):
    def decorator(cls):
        for ext in extensions:
            _PARSER_REGISTRY[ext] = cls
        return cls
    return decorator


def get_parser(file_path: str) -> Optional[Type["BaseParser"]]:
    _discover_parsers()
    _, ext = os.path.splitext(file_path)
    return _PARSER_REGISTRY.get(ext)


def list_supported_extensions() -> List[str]:
    _discover_parsers()
    return list(_PARSER_REGISTRY.keys())


class BaseParser:
    """Base class for all language parsers."""

    def extract_dependencies(
        self, file_path: str, base_dir: str
    ) -> Dict[str, List[str]]:
        raise NotImplementedError

    def extract_entry_points(
        self, file_path: str, base_dir: str
    ) -> List[str]:
        return []
