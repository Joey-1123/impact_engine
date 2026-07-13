from __future__ import annotations

import os
import re
from typing import Dict, List

from core.parsers import register_parser, BaseParser


@register_parser(".go")
class GoParser(BaseParser):
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

        import_block = False
        single_import = re.compile(r'^\s*import\s+(?:\.\s+)?["]([^"]+)["]\s*$')
        import_multi = re.compile(r'^\s*["]([^"]+)["]\s*$')
        import_alias = re.compile(r'^\s*(\w+)\s+["]([^"]+)["]\s*$')

        func_decl = re.compile(r'^\s*func\s+(?:\([^)]*\)\s+)?(\w+)\s*\(')
        blank_id = re.compile(r'^\s*func\s+(?:\([^)]*\)\s+)?_\s*\(')
        call_pattern = re.compile(r'(?:^|[^.])\b([a-zA-Z_]\w*)\.(\w+)\(')
        local_call = re.compile(r'(?<![\w.])\b([a-z]\w*)\s*\(')

        for line in lines:
            stripped = line.strip()

            if stripped == "import (":
                import_block = True
                continue
            if import_block and stripped == ")":
                import_block = False
                continue

            if import_block:
                m = import_alias.match(stripped)
                if m:
                    imports[m.group(1)] = os.path.basename(m.group(2))
                    continue
                m = import_multi.match(stripped)
                if m:
                    pkg = os.path.basename(m.group(1))
                    imports[pkg] = m.group(1)
                continue

            m = single_import.match(stripped)
            if m:
                pkg = os.path.basename(m.group(1))
                imports[pkg] = m.group(1)
                continue

            if blank_id.match(stripped):
                continue

            m = func_decl.match(stripped)
            if m:
                current_func = f"{rel_path}::{m.group(1)}"
                dependencies.setdefault(current_func, set())
                continue

            if current_func:
                for cm in call_pattern.finditer(stripped):
                    pkg_part = cm.group(1)
                    func_part = cm.group(2)
                    if pkg_part in imports:
                        callee = f"{imports[pkg_part]}::{func_part}"
                        dependencies[current_func].add(callee)

                for lm in local_call.finditer(stripped):
                    name = lm.group(1)
                    if name in ("if", "for", "range", "switch", "select", "return",
                                "go", "defer", "chan", "map", "nil", "true", "false",
                                "cap", "len", "make", "new", "append", "copy",
                                "close", "delete", "panic", "recover", "print",
                                "println", "error", "string", "int", "bool",
                                "byte", "rune", "float64", "uintptr"):
                        continue
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
        if re.search(r'func\s+main\s*\(', content):
            return [f"{rel_path}::main"]
        return []
