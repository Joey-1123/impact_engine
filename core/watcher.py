# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import os
import time
from typing import Set, Callable, Optional, Dict


def _get_python_files_flat(base_dir: str) -> Set[str]:
    result: Set[str] = set()
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {
            ".venv", "venv", "env", "__pycache__", "node_modules", "build", "dist",
        }]
        for f in files:
            if f.endswith(".py"):
                result.add(os.path.join(root, f))
    return result


def _snapshot_mtimes(files: Set[str]) -> dict:
    mtimes = {}
    for f in files:
        try:
            mtimes[f] = os.path.getmtime(f)
        except OSError:
            continue
    return mtimes


def watch(
    base_dir: str,
    on_change: Callable[[Set[str]], None],
    interval: float = 1.0,
    max_loops: Optional[int] = None,
) -> None:
    files = _get_python_files_flat(base_dir)
    mtimes = _snapshot_mtimes(files)

    loops = 0
    try:
        while max_loops is None or loops < max_loops:
            time.sleep(interval)
            loops += 1

            current_files = _get_python_files_flat(base_dir)
            current_mtimes = _snapshot_mtimes(current_files)

            changed: Set[str] = set()
            removed = files - current_files

            changed.update(removed)

            for f in current_files:
                if f not in mtimes or mtimes[f] != current_mtimes.get(f):
                    changed.add(f)

            if changed:
                on_change(changed)

            files = current_files
            mtimes = current_mtimes

    except KeyboardInterrupt:
        print("\nWatch mode stopped.")


def _parse_file_deps(file_path: str, base_dir: str) -> Dict[str, Set[str]]:
    from core.extractor import extract_dependencies
    try:
        deps, _, _, _ = extract_dependencies(file_path, base_dir)
        return {k: set(v) for k, v in deps.items()}
    except Exception:
        return {}


def incremental_watch(
    base_dir: str,
    on_change: Callable[[Set[str]], None],
    interval: float = 1.0,
    max_loops: Optional[int] = None,
) -> None:
    from core.file_loader import get_python_files
    from core.graph_builder import build_graph
    from core.extractor import extract_project_dependencies

    files = set(get_python_files(base_dir))
    mtimes = _snapshot_mtimes(files)

    deps = extract_project_dependencies(base_dir)
    graph = build_graph(deps)

    loops = 0
    try:
        while max_loops is None or loops < max_loops:
            time.sleep(interval)
            loops += 1

            current_files = set(get_python_files(base_dir))
            current_mtimes = _snapshot_mtimes(current_files)

            changed: Set[str] = set()
            removed = files - current_files
            changed.update(removed)

            for f in current_files:
                if f not in mtimes or mtimes[f] != current_mtimes.get(f):
                    changed.add(f)

            if changed:
                for f in changed:
                    if f in current_files and os.path.isfile(f):
                        new_deps = _parse_file_deps(f, base_dir)
                        for func, calls in new_deps.items():
                            deps[func] = list(calls)
                        removed_keys = [k for k in deps if k.split("::")[0] == os.path.relpath(f, base_dir).replace("\\", "/") and k not in new_deps]
                        for k in removed_keys:
                            del deps[k]
                    else:
                        rel = os.path.relpath(f, base_dir).replace("\\", "/")
                        removed_keys = [k for k in deps if k.startswith(rel)]
                        for k in removed_keys:
                            del deps[k]

                graph = build_graph(deps)
                on_change(changed)

            files = current_files
            mtimes = current_mtimes

    except KeyboardInterrupt:
        print("\nIncremental watch mode stopped.")
