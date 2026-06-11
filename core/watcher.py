import os
import time
from typing import Set, Callable, Optional


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
    return {f: os.path.getmtime(f) for f in files if os.path.isfile(f)}


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
            added = current_files - files

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
