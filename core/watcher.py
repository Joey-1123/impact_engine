# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import os
import time
from typing import Set, Callable, Optional, Dict

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None


IGNORE_DIRS = {".venv", "venv", "env", "__pycache__", "node_modules", "build", "dist", ".git"}


def _get_python_files_flat(base_dir: str) -> Set[str]:
    result: Set[str] = set()
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS]
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


def _poll_loop(
    base_dir: str,
    on_change: Callable[[Set[str]], None],
    interval: float,
    max_loops: Optional[int],
    respect_gitignore: bool = False,
    incremental: bool = False,
) -> None:
    if incremental:
        from core.file_loader import get_python_files
        from core.graph_builder import build_graph
        from core.extractor import extract_project_dependencies
        files = set(get_python_files(base_dir, respect_gitignore=respect_gitignore))
        mtimes = _snapshot_mtimes(files)
        deps = extract_project_dependencies(base_dir, respect_gitignore=respect_gitignore)
        graph = build_graph(deps)
    else:
        files = _get_python_files_flat(base_dir)
        mtimes = _snapshot_mtimes(files)
        deps = None

    loops = 0
    try:
        while max_loops is None or loops < max_loops:
            time.sleep(interval)
            loops += 1

            if incremental:
                from core.file_loader import get_python_files
                current_files = set(get_python_files(base_dir, respect_gitignore=respect_gitignore))
            else:
                current_files = _get_python_files_flat(base_dir)
            current_mtimes = _snapshot_mtimes(current_files)

            changed: Set[str] = set()
            removed = files - current_files
            changed.update(removed)

            for f in current_files:
                if f not in mtimes or mtimes[f] != current_mtimes.get(f):
                    changed.add(f)

            if changed:
                if incremental and deps is not None:
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
        print("\nWatch mode stopped.")


def _parse_file_deps(file_path: str, base_dir: str) -> Dict[str, Set[str]]:
    from core.extractor import extract_dependencies
    try:
        deps, _, _, _ = extract_dependencies(file_path, base_dir)
        return {k: set(v) for k, v in deps.items()}
    except Exception:
        return {}


def watch(
    base_dir: str,
    on_change: Callable[[Set[str]], None],
    interval: float = 1.0,
    max_loops: Optional[int] = None,
) -> None:
    if Observer is not None:
        _watch_with_watchdog(base_dir, on_change)
    else:
        _poll_loop(base_dir, on_change, interval, max_loops)


def incremental_watch(
    base_dir: str,
    on_change: Callable[[Set[str]], None],
    interval: float = 1.0,
    max_loops: Optional[int] = None,
    respect_gitignore: bool = True,
) -> None:
    if Observer is not None:
        _watch_with_watchdog(base_dir, on_change)
    else:
        _poll_loop(base_dir, on_change, interval, max_loops, respect_gitignore=respect_gitignore, incremental=True)


def _watch_with_watchdog(
    base_dir: str,
    on_change: Callable[[Set[str]], None],
) -> None:
    class ImpactHandler(FileSystemEventHandler):
        def __init__(self):
            self.changed: Set[str] = set()

        def on_modified(self, event):
            if not event.is_directory and event.src_path.endswith(".py"):
                self.changed.add(event.src_path)

        def on_created(self, event):
            if not event.is_directory and event.src_path.endswith(".py"):
                self.changed.add(event.src_path)

        def on_deleted(self, event):
            if not event.is_directory and event.src_path.endswith(".py"):
                self.changed.add(event.src_path)

    observer = Observer()
    handler = ImpactHandler()
    observer.schedule(handler, base_dir, recursive=True)
    observer.start()

    print(f"Watching {base_dir} for changes using watchdog... (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(0.5)
            if handler.changed:
                changed = handler.changed.copy()
                handler.changed.clear()
                on_change(changed)
    except KeyboardInterrupt:
        print("\nWatch mode stopped.")
    finally:
        observer.stop()
        observer.join()
