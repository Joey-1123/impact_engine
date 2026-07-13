# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import shlex
import subprocess
import os
import sys
from typing import Dict, List, Optional, Set


def run_git(args: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        cwd=cwd
    )


def get_current_branch(cwd: Optional[str] = None) -> str:
    try:
        result = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
        return result.stdout.strip() if result.returncode == 0 else "HEAD"
    except Exception:
        return "HEAD"


def get_merge_base(ref_a: str, ref_b: str, cwd: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "merge-base", shlex.quote(ref_a), shlex.quote(ref_b)],
            capture_output=True, text=True, encoding="utf-8", cwd=cwd,
            timeout=60,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Failed to get merge base: {e}", file=sys.stderr)
    return None


def get_changed_files(ref: Optional[str] = None, cwd: Optional[str] = None) -> List[str]:
    try:
        files: List[str] = []

        if ref is None:
            result = run_git(["status", "--porcelain", "-uall"], cwd=cwd)
            if result.returncode != 0:
                return []

            for line in result.stdout.splitlines():
                if len(line) < 4:
                    continue

                status = line[:2]
                path = line[3:]

                if " -> " in path:
                    path = path.split(" -> ", 1)[-1]

                if status != "DD":
                    files.append(path)
        else:
            result = run_git(["diff", "--name-only", shlex.quote(ref)], cwd=cwd)
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
        func_file_path = os.path.normpath(func.split("::")[0])

        if any(os.path.normpath(f) == func_file_path for f in files):
            changed_funcs.append(func)

    return sorted(set(changed_funcs))


def get_changed_functions(
    deps: Dict[str, List[str]],
    ref: Optional[str] = None,
    cwd: Optional[str] = None,
) -> List[str]:
    files = get_changed_files(ref, cwd=cwd)
    return map_files_to_functions(files, deps)
