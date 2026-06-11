# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import os
import pickle
from typing import Dict, List, Set, Tuple
from core.extractor import extract_dependencies


def _cache_path(base_dir: str) -> str:
    return os.path.join(base_dir, ".impact_cache")


def _load_cache(cache_file: str) -> dict:
    if os.path.isfile(cache_file):
        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache_file: str, cache: dict) -> None:
    try:
        with open(cache_file, "wb") as f:
            pickle.dump(cache, f)
    except Exception:
        pass


def extract_project_dependencies_cached(
    path: str,
    use_cache: bool = True,
) -> Tuple[Dict[str, List[str]], Dict[str, int], Dict[str, int]]:
    from core.file_loader import get_python_files

    all_dependencies: Dict[str, Set[str]] = {}
    all_linenos: Dict[str, int] = {}
    all_complexities: Dict[str, int] = {}

    if os.path.isfile(path):
        files = [path]
        base_dir = os.path.dirname(path) or "."
    else:
        files = get_python_files(path)
        base_dir = path

    cache_file = _cache_path(base_dir)
    cache = _load_cache(cache_file) if use_cache else {}

    for file in files:
        file_mtime = os.path.getmtime(file)
        file_key = os.path.relpath(file, base_dir)

        cached = cache.get(file_key)
        if cached and cached.get("mtime") == file_mtime:
            deps = cached["deps"]
            linenos = cached["linenos"]
            complexities = cached["complexities"]
        else:
            try:
                deps, _, linenos, complexities = extract_dependencies(file, base_dir)
                if use_cache:
                    cache[file_key] = {
                        "mtime": file_mtime,
                        "deps": deps,
                        "linenos": linenos,
                        "complexities": complexities,
                    }
            except Exception as e:
                print(f"Error parsing {file}", file=__import__('sys').stderr)
                continue

        for func, calls in deps.items():
            if func not in all_dependencies:
                all_dependencies[func] = set()
            all_dependencies[func].update(calls)

        all_linenos.update(linenos)
        all_complexities.update(complexities)

    if use_cache:
        _save_cache(cache_file, cache)

    return {k: list(v) for k, v in all_dependencies.items()}, all_linenos, all_complexities
