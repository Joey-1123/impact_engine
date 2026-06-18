# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import ast
import os
import sys
from typing import Optional, Set, Dict, List, Tuple
from core.path_resolver import module_to_file

STDLIB_MODULES = {
    "os", "sys", "re", "json", "math", "datetime", "collections", "itertools",
    "functools", "pathlib", "typing", "abc", "enum", "hashlib", "uuid",
    "subprocess", "shutil", "tempfile", "argparse", "logging", "warnings",
    "traceback", "inspect", "textwrap", "string", "random", "statistics",
    "decimal", "fractions", "io", "base64", "binascii", "copy", "pprint",
    "heapq", "bisect", "array", "weakref", "types", "importlib", "pickle",
    "shelve", "marshal", "dbm", "sqlite3", "csv", "configparser", "netrc",
    "plistlib", "zipfile", "tarfile", "gzip", "bz2", "lzma", "http",
    "urllib", "socketserver", "socket", "ssl", "email", "xml", "html",
    "webbrowser", "cgi", "wsgiref", "venv", "ensurepip", "unittest",
    "doctest", "profile", "pstats", "timeit", "calendar", "locale",
    "gettext", "struct", "codecs", "dataclasses", "contextlib", "ast",
    "asyncio", "threading", "multiprocessing", "concurrent", "signal",
    "mmap", "ctypes", "platform", "errno", "stat", "filecmp", "glob",
    "fnmatch", "linecache", "dis", "tokenize", "keyword", "token",
    "symbol", "symtable", "opcode", "compileall", "py_compile",
    "zipapp", "pdb", "bdb", "cmd", "code", "rlcompleter",
}


def _is_stdlib_module(module_name: str) -> bool:
    base = module_name.split(".")[0]
    if base in STDLIB_MODULES:
        return True
    try:
        return base in sys.stdlib_module_names
    except AttributeError:
        return False


def _is_name_equals_main(node):
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    if len(node.test.ops) != 1 or len(node.test.comparators) != 1:
        return False
    if not isinstance(node.test.ops[0], ast.Eq):
        return False
    left = node.test.left
    right = node.test.comparators[0]
    if isinstance(left, ast.Name) and isinstance(right, ast.Constant):
        return left.id == "__name__" and right.value == "__main__"
    if isinstance(right, ast.Name) and isinstance(left, ast.Constant):
        return left.value == "__main__" and right.id == "__name__"
    return False


def _compute_cyclomatic_complexity(node: ast.FunctionDef) -> int:
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, ast.Assert):
            complexity += 1
    return complexity


class DependencyExtractor(ast.NodeVisitor):
    def __init__(self, file_path: str, base_dir: str):
        self.base_dir = base_dir
        self.file_name = self._normalize_path(file_path)
        self.dependencies: Dict[str, Set[str]] = {}
        self.current_function: Optional[str] = None
        self.imports: Dict[str, str] = {}
        self.defined_functions: Set[str] = set()
        self.current_class: Optional[str] = None
        self.main_block_functions: Set[str] = set()
        self._in_main_block: bool = False
        self.function_linenos: Dict[str, int] = {}
        self.function_complexity: Dict[str, int] = {}

    def is_project_path(self, path: str) -> bool:
        if not path:
            return False
        file_path = path.split("::")[0] if "::" in path else path
        abs_path = os.path.normpath(os.path.join(self.base_dir, file_path))
        return (
            os.path.isfile(abs_path)
            and abs_path.startswith(os.path.normpath(self.base_dir))
        )

    def _normalize_path(self, target_path: str) -> Optional[str]:
        if not target_path:
            return None
        if not os.path.isabs(target_path):
            target_path = os.path.join(self.base_dir, target_path)
        rel_path = os.path.relpath(target_path, self.base_dir)
        return rel_path.replace("\\", "/")

    def _resolve_relative_module(self, module: str, current_file: str) -> Optional[str]:
        if not module or not module.startswith("."):
            return module
        if not current_file:
            return None
        parts = current_file.replace("\\", "/").split("/")
        depth = len(module) - len(module.lstrip("."))
        module_name = module[depth:]
        if len(parts) > depth:
            base = "/".join(parts[:-depth]) if depth > 0 else "/".join(parts[:-1])
            if module_name:
                return base.replace("/", ".") + "." + module_name
            return base.replace("/", ".")
        return None

    def _process_decorators(self, node: ast.FunctionDef) -> None:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                deco_name = self._get_call_name(decorator)
            elif isinstance(decorator, (ast.Name, ast.Attribute)):
                deco_name = self._get_call_name(
                    ast.Call(func=decorator, args=[], keywords=[], lineno=0, col_offset=0)
                )
            else:
                continue

            if not deco_name:
                continue

            namespaced_call: Optional[str] = None
            if deco_name in self.imports:
                namespaced_call = self.imports[deco_name]
            elif "." in deco_name:
                module, func = deco_name.split(".", 1)
                if module in self.imports:
                    base = self.imports[module]
                    if "::" not in base:
                        namespaced_call = f"{base}::{func}"
                    else:
                        namespaced_call = base
            else:
                if deco_name in self.defined_functions:
                    namespaced_call = f"{self.file_name}::{deco_name}"

            if namespaced_call and self.is_project_path(namespaced_call):
                func_id = f"{self.file_name}::{node.name}"
                if func_id not in self.dependencies:
                    self.dependencies[func_id] = set()
                self.dependencies[func_id].add(namespaced_call)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defined_functions.add(node.name)
        if self.current_class:
            func_id = f"{self.file_name}::{self.current_class}.{node.name}"
        else:
            func_id = f"{self.file_name}::{node.name}"
        self.function_linenos[func_id] = node.lineno
        self.function_complexity[func_id] = _compute_cyclomatic_complexity(node)
        self.current_function = func_id
        self._process_decorators(node)
        if self.current_function not in self.dependencies:
            self.dependencies[self.current_function] = set()
        self.generic_visit(node)
        self.current_function = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.defined_functions.add(node.name)
        if self.current_class:
            func_id = f"{self.file_name}::{self.current_class}.{node.name}"
        else:
            func_id = f"{self.file_name}::{node.name}"
        self.function_linenos[func_id] = node.lineno
        self.function_complexity[func_id] = _compute_cyclomatic_complexity(node)
        self.current_function = func_id
        self._process_decorators(node)
        if self.current_function not in self.dependencies:
            self.dependencies[self.current_function] = set()
        self.generic_visit(node)
        self.current_function = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old_class = self.current_class
        self.current_class = node.name
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_id = f"{self.file_name}::{self.current_class}.{child.name}"
                self.defined_functions.add(method_id)
        self.generic_visit(node)
        self.current_class = old_class

    def visit_If(self, node: ast.If) -> None:
        if _is_name_equals_main(node):
            old_in_main = self._in_main_block
            self._in_main_block = True
            for stmt in node.body:
                for child in ast.walk(stmt):
                    if isinstance(child, ast.Call):
                        caller_name = self._get_call_name(child)
                        if caller_name and caller_name in self.defined_functions:
                            self.main_block_functions.add(f"{self.file_name}::{caller_name}")
            self.generic_visit(node)
            self._in_main_block = old_in_main
        else:
            self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self.current_function:
            func_name = self._get_call_name(node)
            if func_name:
                namespaced_call: Optional[str] = None

                if func_name in self.imports:
                    namespaced_call = self.imports[func_name]

                elif "." in func_name:
                    module, call_func = func_name.split(".", 1)

                    if module in self.imports:
                        base = self.imports[module]
                        if "::" not in base:
                            namespaced_call = f"{base}::{call_func}"
                        else:
                            base_file = base.split("::")[0]
                            namespaced_call = f"{base_file}::{call_func}"

                    elif module in ("self", "cls") and self.current_class:
                        method = f"{self.current_class}.{call_func}"
                        if method in self.defined_functions:
                            namespaced_call = f"{self.file_name}::{method}"
                        elif call_func in self.defined_functions:
                            namespaced_call = f"{self.file_name}::{method}"

                else:
                    if func_name in self.defined_functions:
                        namespaced_call = f"{self.file_name}::{func_name}"

                if namespaced_call and self.is_project_path(namespaced_call):
                    self.dependencies[self.current_function].add(namespaced_call)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module
        if module and module.startswith("."):
            module = self._resolve_relative_module(module, self.file_name)

        for alias in node.names:
            name = alias.name
            asname = alias.asname or name

            if name == "*":
                continue

            if module:
                if _is_stdlib_module(module):
                    continue

                file_path = module_to_file(module, self.base_dir)
                normalized_path = self._normalize_path(file_path)

                if normalized_path:
                    self.imports[asname] = f"{normalized_path}::{name}"

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.name
            asname = alias.asname or name

            if _is_stdlib_module(name):
                continue

            file_path = module_to_file(name, self.base_dir)
            normalized_path = self._normalize_path(file_path)

            if normalized_path:
                self.imports[asname] = normalized_path

        self.generic_visit(node)

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            value = node.func.value
            if isinstance(value, ast.Name):
                return f"{value.id}.{node.func.attr}"
            return node.func.attr
        return None


def extract_dependencies(file_path: str, base_dir: str) -> Tuple[Dict[str, List[str]], Set[str], Dict[str, int], Dict[str, int]]:
    with open(file_path, "r", encoding="utf-8", errors="surrogateescape") as f:
        tree = ast.parse(f.read())

    extractor = DependencyExtractor(file_path, base_dir)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            extractor.defined_functions.add(node.name)

    extractor.visit(tree)

    deps = {k: list(v) for k, v in extractor.dependencies.items()}
    return deps, extractor.main_block_functions, extractor.function_linenos, extractor.function_complexity


def extract_project_dependencies(path: str) -> Dict[str, List[str]]:
    from core.file_loader import get_python_files

    all_dependencies: Dict[str, Set[str]] = {}

    if os.path.isfile(path):
        files = [path]
        base_dir = os.path.dirname(path) or "."
    else:
        files = get_python_files(path)
        base_dir = path

    for file in files:
        try:
            deps, _, _, _ = extract_dependencies(file, base_dir)

            for func, calls in deps.items():
                if func not in all_dependencies:
                    all_dependencies[func] = set()
                all_dependencies[func].update(calls)

        except Exception as e:
            print(f"Error parsing {file}: {e}", file=sys.stderr)

    return {k: list(v) for k, v in all_dependencies.items()}


def extract_project_dependencies_rich(path: str) -> Tuple[Dict[str, List[str]], Dict[str, int], Dict[str, int]]:
    from core.file_loader import get_python_files

    all_dependencies: Dict[str, Set[str]] = {}
    all_linenos: Dict[str, int] = {}
    all_complexities: Dict[str, int] = {}

    if os.path.isfile(path):
        files = [path]
        base_dir = os.path.dirname(path) or "."
    else:
        files = get_python_files(path)
        base_dir = path

    for file in files:
        try:
            deps, _, linenos, complexities = extract_dependencies(file, base_dir)

            for func, calls in deps.items():
                if func not in all_dependencies:
                    all_dependencies[func] = set()
                all_dependencies[func].update(calls)

            all_linenos.update(linenos)
            all_complexities.update(complexities)

        except Exception as e:
            print(f"Error parsing {file}: {e}", file=sys.stderr)

    return {k: list(v) for k, v in all_dependencies.items()}, all_linenos, all_complexities


def extract_project_entry_points(path: str) -> List[str]:
    from core.file_loader import get_python_files

    all_entry_points: Set[str] = set()

    if os.path.isfile(path):
        files = [path]
        base_dir = os.path.dirname(path) or "."
    else:
        files = get_python_files(path)
        base_dir = path

    for file in files:
        try:
            _, entry_funcs, _, _ = extract_dependencies(file, base_dir)
            all_entry_points.update(entry_funcs)
        except Exception as e:
            print(f"Error parsing {file}: {e}", file=sys.stderr)

    return sorted(all_entry_points)
