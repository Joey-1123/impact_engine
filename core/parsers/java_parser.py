# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
"""
Java parser for impact-engine.

Requires: pip install tree-sitter tree-sitter-java

TODO: Implement proper AST parsing with tree-sitter.
Currently returns empty dependencies as a stub for the plugin architecture.
"""
import sys
from typing import Dict, List
from core.parsers import register_parser, BaseParser


@register_parser(".java")
class JavaParser(BaseParser):
    def extract_dependencies(
        self, file_path: str, base_dir: str
    ) -> Dict[str, List[str]]:
        print(f"Warning: Java parser is a stub — no dependency analysis for {file_path}", file=sys.stderr)
        return {}

    def extract_entry_points(
        self, file_path: str, base_dir: str
    ) -> List[str]:
        return []
