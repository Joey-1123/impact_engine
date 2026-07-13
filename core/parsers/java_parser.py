from __future__ import annotations

import os
import re
from typing import Dict, List

from core.parsers import register_parser, BaseParser


@register_parser(".java")
class JavaParser(BaseParser):
    def extract_dependencies(
        self, file_path: str, base_dir: str
    ) -> Dict[str, List[str]]:
        rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
        dependencies: Dict[str, set] = {}
        current_method: str = ""
        imports: Dict[str, str] = {}
        class_name: str = ""

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return {}

        import_pattern = re.compile(r'^\s*import\s+(?:static\s+)?([a-zA-Z0-9_.]+);')
        class_pattern = re.compile(r'^\s*(?:public\s+|protected\s+|private\s+)?(?:abstract\s+|final\s+)?(?:class|interface|enum)\s+(\w+)')
        java_modifiers = r'(?:public|protected|private|static|final|abstract|synchronized|native|transient|volatile|default)\s+'
        method_pattern = re.compile(
            r'^\s*(?:' + java_modifiers + r')*'
            r'(?:<[^>]+>\s+)?'
            r'(?:[a-zA-Z_]\w*(?:\[\])*(?:\.\.\.)?)\s+'
            r'(\w+)\s*\('
        )
        simple_method = re.compile(r'^\s*(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+(?:\s*,\s*\w+)*)?\s*\{')
        call_pattern = re.compile(r'(\w+)\.(\w+)\(')
        local_call = re.compile(r'(?<![\w.])\b([a-z]\w*)\s*\(')

        for line in lines:
            stripped = line.strip()

            m = import_pattern.match(stripped)
            if m:
                full_path = m.group(1)
                simple = full_path.split(".")[-1]
                imports[simple] = full_path
                continue

            m = class_pattern.match(stripped)
            if m:
                class_name = m.group(1)
                continue

            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*") or stripped.startswith("@Override"):
                continue

            m = method_pattern.match(stripped)
            if not m:
                m = simple_method.match(stripped)
            if m and m.group(1) != class_name:
                method_name = m.group(1)
                full_method = f"{rel_path}::{class_name}.{method_name}" if class_name else f"{rel_path}::{method_name}"
                current_method = full_method
                dependencies.setdefault(current_method, set())
                continue

            if current_method:
                for cm in call_pattern.finditer(stripped):
                    obj = cm.group(1)
                    method = cm.group(2)
                    if obj in imports:
                        callee = f"{imports[obj]}::{method}"
                        dependencies[current_method].add(callee)

                for lm in local_call.finditer(stripped):
                    name = lm.group(1)
                    if name in ("if", "for", "while", "switch", "catch", "return",
                                "throw", "new", "try", "null", "this", "super",
                                "true", "false", "assert", "synchronized", "instanceof",
                                "int", "long", "double", "float", "boolean", "char",
                                "byte", "short", "void", "final", "static", "public",
                                "private", "protected", "extends", "implements"):
                        continue
                    callee = f"{rel_path}::{name}"
                    dependencies[current_method].add(callee)

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
        if re.search(r'\bpublic\s+static\s+void\s+main\b', content):
            return [f"{rel_path}::main"]
        return []
