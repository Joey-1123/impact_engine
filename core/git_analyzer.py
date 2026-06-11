import subprocess
import os
from typing import Dict, List, Optional, Set


def _run_git(args: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        cwd=cwd
    )


def get_changed_files(ref: Optional[str] = None, cwd: Optional[str] = None) -> List[str]:
    try:
        files: List[str] = []

        if ref is None:
            result = _run_git(["status", "--porcelain", "-uall"], cwd=cwd)
            if result.returncode != 0:
                return []

            for line in result.stdout.splitlines():
                if len(line) < 4:
                    continue

                status = line[:2]
                path = line[3:]

                if " -> " in path:
                    path = path.split(" -> ", 1)[-1]

                if status == "??" or status[0] != "D" or status[1] != "D":
                    files.append(path)
        else:
            result = _run_git(["diff", "--name-only", ref], cwd=cwd)
            if result.returncode != 0:
                return []

            files = result.stdout.strip().splitlines()

        IGNORE_FOLDERS: Set[str] = {"tests", "build", "__pycache__", ".venv"}
        valid_files: List[str] = []

        for f in files:
            if not f.endswith((".py", ".js")):
                continue

            path_parts = set(f.split('/'))

            if not IGNORE_FOLDERS.intersection(path_parts):
                valid_files.append(f)

        return valid_files

    except FileNotFoundError:
        return []
    except Exception:
        return []


def map_files_to_functions(files: List[str], deps: Dict[str, List[str]]) -> List[str]:
    if not files:
        return []

    changed_funcs: List[str] = []

    for func in deps.keys():
        func_file_path = func.split("::")[0]

        if any(f.endswith(func_file_path) for f in files):
            changed_funcs.append(func)

    return sorted(set(changed_funcs))


def get_changed_functions(
    deps: Dict[str, List[str]],
    ref: Optional[str] = None,
    cwd: Optional[str] = None,
) -> List[str]:
    files = get_changed_files(ref, cwd=cwd)
    return map_files_to_functions(files, deps)
