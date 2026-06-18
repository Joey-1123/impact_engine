# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from typing import Dict, List, Set, Tuple
from core.parsers import register_parser, BaseParser
from core.extractor import extract_dependencies, extract_project_entry_points


@register_parser(".py")
class PythonParser(BaseParser):
    def extract_dependencies(
        self, file_path: str, base_dir: str
    ) -> Dict[str, List[str]]:
        deps, _, _, _ = extract_dependencies(file_path, base_dir)
        return deps

    def extract_entry_points(
        self, file_path: str, base_dir: str
    ) -> List[str]:
        return extract_project_entry_points(file_path)
