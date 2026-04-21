import ast
import os

class DependencyExtractor(ast.NodeVisitor):
    def __init__(self):
        self.dependencies = {}  # {function: [calls]}
        self.current_function = None

    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.dependencies[self.current_function] = []

        # Visit inside function body
        self.generic_visit(node)

        self.current_function = None

    def visit_Call(self, node):
        if self.current_function:
            func_name = self._get_call_name(node)
            if func_name:
                self.dependencies[self.current_function].append(func_name)

        self.generic_visit(node)

    def _get_call_name(self, node):
        """
        Extract function name from call node.
        Handles:
        - simple calls: func()
        - attribute calls: obj.method()
        """
        if isinstance(node.func, ast.Name):
            return node.func.id

        elif isinstance(node.func, ast.Attribute):
            return node.func.attr

        return None


def extract_dependencies(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    extractor = DependencyExtractor()
    extractor.visit(tree)

    return extractor.dependencies


def extract_project_dependencies(path):
    from core.file_loader import get_python_files

    all_dependencies = {}

    files = []

    if os.path.isfile(path):
        files = [path]
    else:
        files = get_python_files(path)

    for file in files:
        try:
            deps = extract_dependencies(file)

            # Merge dependencies
            for func, calls in deps.items():
                if func not in all_dependencies:
                    all_dependencies[func] = []

                all_dependencies[func].extend(calls)

        except Exception as e:
            print(f"Error parsing {file}: {e}")

    return all_dependencies