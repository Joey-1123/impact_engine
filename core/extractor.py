import ast
import os


class DependencyExtractor(ast.NodeVisitor):
    def __init__(self, file_name):
        self.file_name = file_name
        self.dependencies = {}
        self.current_function = None
        self.imports = {} 

    def visit_FunctionDef(self, node):
        func_id = f"{self.file_name}::{node.name}"

        self.current_function = func_id
        self.dependencies[self.current_function] = []

        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        if self.current_function:
            func_name = self._get_call_name(node)
            if func_name:
                # ✅ resolve imports
                if func_name in self.imports:
                    namespaced_call = self.imports[func_name]
                else:
                    namespaced_call = f"{self.file_name}::{func_name}"

                self.dependencies[self.current_function].append(namespaced_call)

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module

        for alias in node.names:
            name = alias.name
            asname = alias.asname or name

            if module:
                self.imports[asname] = f"{module}.py::{name}"

        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.name
            asname = alias.asname or name

            self.imports[asname] = f"{name}.py"

        self.generic_visit(node)

    def _get_call_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None


def extract_dependencies(file_path):
    file_name = os.path.basename(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    extractor = DependencyExtractor(file_name)
    extractor.visit(tree)

    return extractor.dependencies


def extract_project_dependencies(path):
    from core.file_loader import get_python_files

    all_dependencies = {}

    if os.path.isfile(path):
        files = [path]
    else:
        files = get_python_files(path)

    for file in files:
        try:
            deps = extract_dependencies(file)

            for func, calls in deps.items():
                if func not in all_dependencies:
                    all_dependencies[func] = []

                all_dependencies[func].extend(calls)

        except Exception as e:
            print(f"Error parsing {file}: {e}")

    return all_dependencies