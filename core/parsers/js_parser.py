# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from typing import Dict, List
from core.parsers import register_parser, BaseParser
from core.js_extractor import extract_js_dependencies


@register_parser(".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")
class JsParser(BaseParser):
    def extract_dependencies(
        self, file_path: str, base_dir: str
    ) -> Dict[str, List[str]]:
        return extract_js_dependencies(file_path, base_dir)
