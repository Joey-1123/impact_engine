import subprocess
import os


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