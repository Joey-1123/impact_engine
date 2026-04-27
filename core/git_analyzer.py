import subprocess
import os

def get_changed_files(ref="HEAD"):
    """
    Returns a list of changed Python and JavaScript files.
    Default: working tree vs HEAD (uncommitted changes).
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

        # Using a set for faster lookups
        IGNORE_FOLDERS = {"tests", "build", "__pycache__", ".venv"}
        valid_files = []

        for f in files:
            if not f.endswith((".py", ".js")):
                continue
            
            # Git always uses '/' as the path separator
            path_parts = set(f.split('/'))
            
            # If the path parts and ignore folders have no common elements
            if not IGNORE_FOLDERS.intersection(path_parts):
                valid_files.append(f)

        return valid_files

    except FileNotFoundError:
        # Git is not installed or not available on PATH.
        return []
    except Exception:
        return []

def map_files_to_functions(files, deps):
    """
    Map changed files -> functions using deps keys.
    deps format: "path/to/sample.py::function" or "sample.py::function"
    """
    if not files:
        return []

    changed_funcs = []

    for func in deps.keys():
        # Extract the file path portion from the dependency key
        func_file_path = func.split("::")[0]

        # Use endswith to match paths more safely than just basenames. 
        # This prevents src/main.py from triggering app/main.py's functions.
        if any(f.endswith(func_file_path) for f in files):
            changed_funcs.append(func)

    return sorted(set(changed_funcs))

def get_changed_functions(deps, ref="HEAD"):
    """
    Main entry point: Retrieves changed files and maps them to affected functions.
    """
    files = get_changed_files(ref)
    return map_files_to_functions(files, deps)