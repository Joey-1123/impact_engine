import ast
import os
import sys  # Required for safe error printing
from core.path_resolver import module_to_file

class DependencyExtractor(ast.NodeVisitor):
    def __init__(self, file_path, base_dir):
        self.base_dir = base_dir
        
        # Standardize the current file's path
        self.file_name = self._normalize_path(file_path)
        
        self.dependencies = {}
        self.current_function = None
        self.imports = {}
        
        # FIX 2: Track defined functions to filter out built-ins/noise
        self.defined_functions = set() 
    
    def is_project_path(self, path):
        if not path:
            return False
            
        return not path.startswith((
            "json.py",
            "ast.py",
            "os.py",
            "sys.py",
            "subprocess.py",
            "django/",
            "rest_framework/",
            "networkx",
            "requests",
        ))

    def _normalize_path(self, target_path):
        """Ensures all paths (local and imported) use the exact same relative format"""
        if not target_path:
            return None
        rel_path = os.path.relpath(target_path, self.base_dir)
        return rel_path.replace("\\", "/")  # Windows fix

    def visit_FunctionDef(self, node):
        self.defined_functions.add(node.name)  # Keep this as a safety net
        func_id = f"{self.file_name}::{node.name}"

        self.current_function = func_id
        if self.current_function not in self.dependencies:
            self.dependencies[self.current_function] = set() # Use set to prevent duplicates

        self.generic_visit(node)
        self.current_function = None

    def visit_AsyncFunctionDef(self, node):
        # Good practice to also track async functions
        self.defined_functions.add(node.name)
        func_id = f"{self.file_name}::{node.name}"

        self.current_function = func_id
        if self.current_function not in self.dependencies:
            self.dependencies[self.current_function] = set()

        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        if self.current_function:
            func_name = self._get_call_name(node)
            if func_name:
                namespaced_call = None

                # 1. Direct imported function: e.g., `helper()`
                if func_name in self.imports:
                    namespaced_call = self.imports[func_name]

                # 2. Module call or Object method: e.g., `utils.helper()` or `user.save()`
                elif "." in func_name:
                    module, func = func_name.split(".", 1)

                    # FIX 4: Only resolves if module is specifically known in imports
                    if module in self.imports:
                        base = self.imports[module]
                        
                        # FIX 3: Improved import resolution
                        if "::" not in base:
                            namespaced_call = f"{base}::{func}"
                        else:
                            namespaced_call = base

                # 3. Local function call: e.g., `local_helper()`
                else:
                    # FIX 1 & 2: Only add if function actually exists in this file
                    if func_name in self.defined_functions:
                        namespaced_call = f"{self.file_name}::{func_name}"

                # Only add if it is a valid project path
                if namespaced_call and self.is_project_path(namespaced_call):
                    # 🔥 Safely print to stderr so it doesn't break the JSON output
                    # print(f"{self.current_function} -> {namespaced_call}", file=sys.stderr)
                    self.dependencies[self.current_function].add(namespaced_call)

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module

        for alias in node.names:
            name = alias.name
            asname = alias.asname or name

            if module:
                file_path = module_to_file(module)
                normalized_path = self._normalize_path(file_path)

                if normalized_path:
                    self.imports[asname] = f"{normalized_path}::{name}"

        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.name
            asname = alias.asname or name

            file_path = module_to_file(name)
            normalized_path = self._normalize_path(file_path)

            if normalized_path:
                self.imports[asname] = normalized_path

        self.generic_visit(node)

    def _get_call_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id

        elif isinstance(node.func, ast.Attribute):
            value = node.func.value
            if isinstance(value, ast.Name):
                return f"{value.id}.{node.func.attr}"
            return node.func.attr

        return None


def extract_dependencies(file_path, base_dir):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    extractor = DependencyExtractor(file_path, base_dir)
    
    # Pre-pass to catch all defined functions before traversing (fixes forward-reference bugs)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            extractor.defined_functions.add(node.name)

    extractor.visit(tree)

    # Convert sets back to lists for JSON serialization compatibility
    return {k: list(v) for k, v in extractor.dependencies.items()}


def extract_project_dependencies(path):
    from core.file_loader import get_python_files

    all_dependencies = {}

    if os.path.isfile(path):
        files = [path]
        base_dir = os.path.dirname(path) or "."
    else:
        files = get_python_files(path)
        base_dir = path

    for file in files:
        try:
            deps = extract_dependencies(file, base_dir)

            for func, calls in deps.items():
                if func not in all_dependencies:
                    all_dependencies[func] = set()
                
                # Using set union to automatically handle duplicates across loops
                all_dependencies[func].update(calls)

        except Exception as e:
            # Safely print errors to stderr
            print(f"Error parsing {file}: {e}", file=sys.stderr)

    # Convert final sets to lists
    return {k: list(v) for k, v in all_dependencies.items()}