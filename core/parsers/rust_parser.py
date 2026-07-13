from __future__ import annotations

import os
import re
from typing import Dict, List

from core.parsers import register_parser, BaseParser


@register_parser(".rs")
class RustParser(BaseParser):
    def extract_dependencies(
        self, file_path: str, base_dir: str
    ) -> Dict[str, List[str]]:
        rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
        dependencies: Dict[str, set] = {}
        current_func: str = ""
        imports: Dict[str, str] = {}

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return {}

        use_pattern = re.compile(r'^\s*use\s+(?:::)?([^;]+);')
        fn_pattern = re.compile(r'^\s*(?:pub\s+)?(?:unsafe\s+)?(?:async\s+)?fn\s+(\w+)')
        call_pattern = re.compile(r'([a-zA-Z_]\w*)::(\w+)\(')
        direct_call = re.compile(r'(?<![\w.:>])\b([a-z_]\w*)\s*\(')

        def _resolve_use(path: str) -> str | None:
            parts = path.split("::")
            if parts[0] in ("crate", "self", "super"):
                return parts[-1]
            return parts[-1]

        for line in lines:
            stripped = line.strip()

            m = use_pattern.match(stripped)
            if m:
                path = m.group(1)
                alias_match = re.search(r'\bas\s+(\w+)$', path)
                if alias_match:
                    name = alias_match.group(1)
                else:
                    name = _resolve_use(path)
                if name and not name[0].isupper():
                    imports[name] = path
                continue

            m = fn_pattern.match(stripped)
            if m:
                current_func = f"{rel_path}::{m.group(1)}"
                dependencies.setdefault(current_func, set())
                continue

            if stripped.startswith("//") or stripped.startswith("#"):
                continue

            if current_func:
                for cm in call_pattern.finditer(stripped):
                    module_part = cm.group(1)
                    func_part = cm.group(2)
                    callee = f"{module_part}::{func_part}"
                    dependencies[current_func].add(callee)

                for dm in direct_call.finditer(stripped):
                    name = dm.group(1)
                    if name in ("if", "for", "while", "match", "let", "mut",
                                "return", "true", "false", "None", "Some", "Ok", "Err",
                                "self", "Self", "as", "in", "ref", "move"):
                        continue
                    if name in imports:
                        callee = f"{imports[name]}::{name}"
                        dependencies[current_func].add(callee)
                    else:
                        callee = f"{rel_path}::{name}"
                        dependencies[current_func].add(callee)

        return {k: sorted(v) for k, v in dependencies.items()}

    def extract_entry_points(
        self, file_path: str, base_dir: str
    ) -> List[str]:
        rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return []
        if re.search(r'\bfn\s+main\b', content):
            return [f"{rel_path}::main"]
        return []
