import subprocess
import os


def get_changed_files(ref="HEAD"):
    """
    Returns changed Python files.
    Dult: working tree vs HEAD (uncommitted changes)
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", ref],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        if result.returncode != 0:
            return []

        files = result.stdout.strip().splitlines()

        IGNORE_FOLDERS = ["tests", "venv", "__pycache__"]

        return [
            f for f in files
            if f.endswith(".py")
             and not any(f.startswith(folder) for folder in IGNORE_FOLDERS)
        ]


    except FileNotFoundError:
        # Git is not installed or not available on PATH.
        return []
    except Exception:
        return []


def map_files_to_functions(files, deps):
    """
    Map changed files → functions using deps keys
    deps format: "sample.py::function"
    """
    if not files:
        return []

    file_names = {os.path.basename(f) for f in files}

    changed_funcs = []

    for func in deps.keys():
        file_name = os.path.basename(func.split("::")[0])

        if file_name in file_names:
            changed_funcs.append(func)

    return sorted(set(changed_funcs))


def get_changed_functions(deps, ref="HEAD"):
    """
    Main function used by API
    """
    files = get_changed_files(ref)
    return map_files_to_functions(files, deps)