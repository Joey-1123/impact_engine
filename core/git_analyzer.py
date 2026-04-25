import subprocess
import os
import ast

def get_changed_files():
    
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True,
        text=True
    )

    files = result.stdout.strip().split("\n")
    return [f for f in files if f.endswith(".py")]


def map_files_to_functions(files, deps):
    
    changed_funcs = []

    for func in deps:
        file_name = func.split("::")[0]

        for file in files:
            if os.path.basename(file) == file_name:
                changed_funcs.append(func)

    return changed_funcs

def get_changed_lines():
    

    result = subprocess.run(
        ["git", "diff", "-U0"],
        capture_output=True,
        text=True
    )

    lines = result.stdout.split("\n")

    file_changes = {}
    current_file = None

    for line in lines:
        if line.startswith("+++ b/"):
            current_file = line.replace("+++ b/", "").strip()
            file_changes[current_file] = set()

        elif line.startswith("@@"):
            # Example: @@ -10,0 +11,3 @@
            parts = line.split(" ")

            for part in parts:
                if part.startswith("+"):
                    part = part[1:]
                    if "," in part:
                        start, count = part.split(",")
                        start = int(start)
                        count = int(count)
                    else:
                        start = int(part)
                        count = 1

                    for i in range(start, start + count):
                        file_changes[current_file].add(i)

    return file_changes

def map_lines_to_functions(file_path, changed_lines):
    
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start = node.lineno
            end = getattr(node, "end_lineno", start)

            for line in changed_lines:
                if start <= line <= end:
                    functions.append(node.name)
                    break

    return functions