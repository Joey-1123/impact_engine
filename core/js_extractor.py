# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import re
import os
from typing import Dict, List, Set


def extract_js_dependencies(file_path: str, base_dir: str) -> Dict[str, List[str]]:
    rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
    dependencies: Dict[str, Set[str]] = {}
    current_function: str = ""

    func_pattern = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)")
    arrow_func = re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(?")
    class_method = re.compile(r"^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{")
    require_pattern = re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*require\(['\"]([^'\"]+)['\"]\)")
    import_pattern = re.compile(r"import\s+(?:\*\s+as\s+)?(\w+)\s+from\s+['\"]([^'\"]+)['\"]")
    import_destructure = re.compile(r"import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]")
    call_pattern = re.compile(r"(\w+)\(|(\w+)\.(\w+)\(")

    imports: Dict[str, str] = {}

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return {}

    for line in lines:
        m = func_pattern.search(line)
        if m:
            current_function = f"{rel_path}::{m.group(1)}"
            if current_function not in dependencies:
                dependencies[current_function] = set()
            continue

        m = arrow_func.search(line)
        if m:
            current_function = f"{rel_path}::{m.group(1)}"
            if current_function not in dependencies:
                dependencies[current_function] = set()
            continue

        m = require_pattern.search(line)
        if m:
            local_name = m.group(1)
            module_path = m.group(2)
            if not module_path.startswith("."):
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(rel_path), module_path))
            imports[local_name] = resolved
            continue

        m = import_pattern.search(line)
        if m:
            local_name = m.group(1)
            module_path = m.group(2)
            if not module_path.startswith("."):
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(rel_path), module_path))
            imports[local_name] = resolved
            continue

        m = import_destructure.search(line)
        if m:
            names = [n.strip() for n in m.group(1).split(",")]
            module_path = m.group(2)
            if module_path.startswith("."):
                resolved = os.path.normpath(os.path.join(os.path.dirname(rel_path), module_path))
                for name in names:
                    imports[name] = f"{resolved}::{name}"
            continue

        if current_function:
            for call in call_pattern.finditer(line):
                if call.group(1) and not call.group(2):
                    func_name = call.group(1)
                    if func_name in ("if", "for", "while", "switch", "return", "throw", "new"):
                        continue
                    callee = f"{rel_path}::{func_name}"
                    if func_name in imports:
                        callee = f"{imports[func_name]}::{func_name}"
                    dependencies[current_function].add(callee)
                elif call.group(2) and call.group(3):
                    obj = call.group(2)
                    method = call.group(3)
                    if obj in imports:
                        callee = f"{imports[obj]}::{method}"
                        dependencies[current_function].add(callee)

    return {k: sorted(v) for k, v in dependencies.items()}
