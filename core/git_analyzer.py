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

    # normalize git paths → only filename
    files = [os.path.basename(f) for f in files]

    for func in deps.keys():
        file_name = os.path.basename(func.split("::")[0])

        if file_name in files:
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
        #  Detect file path
        if line.startswith("+++ b/"):
            file_path = line.replace("+++ b/", "").strip()

            #  Only process Python files
            if not file_path.endswith(".py"):
                current_file = None
                continue

            #  Skip /dev/null (deleted files case)
            if file_path == "/dev/null":
                current_file = None
                continue

            current_file = file_path
            file_changes[current_file] = set()

        #  Parse hunk header
        elif line.startswith("@@") and current_file:
            parts = line.split(" ")

            for part in parts:
                if part.startswith("+") and not part.startswith("+++"):
                    part = part[1:]

                    try:
                        if "," in part:
                            start, count = part.split(",")
                            start = int(start)
                            count = int(count)
                        else:
                            start = int(part)
                            count = 1

                        for i in range(start, start + count):
                            file_changes[current_file].add(i)

                    except ValueError:
                        #  Ignore malformed diff segments
                        continue

    return file_changes
def map_lines_to_functions(file_path, changed_lines):
    # 🔒 Step 1: ensure it's a Python file
    if not file_path.endswith(".py"):
        return []

    # 🔒 Step 2: ensure file exists
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

    except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
        # 🚫 Skip invalid or non-parsable files
        return []

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start = node.lineno
            end = getattr(node, "end_lineno", start)

            # ⚡ Efficient check using intersection
            if any(start <= line <= end for line in changed_lines):
                functions.append(node.name)

    return functions