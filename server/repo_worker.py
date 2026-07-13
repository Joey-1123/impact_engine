from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from core.extractor import extract_project_dependencies_rich
from core.graph_builder import build_graph
from core.detector import find_entry_points, find_cycles
from core.analyzer import find_dead_code
from core.git_analyzer import get_changed_functions

_cache: dict[str, dict[str, Any]] = {}


def _analyze_sync(repo_path: Path) -> dict[str, Any]:
    deps, linenos, complexities = extract_project_dependencies_rich(str(repo_path))
    graph = build_graph(deps)
    changed_funcs = get_changed_functions(deps)
    entry_points = find_entry_points(graph)
    dead_nodes = find_dead_code(graph, entry_points)
    cycles = find_cycles(graph)

    total_files = len(deps)
    total_functions = graph.number_of_nodes()
    languages: dict[str, int] = {}
    for fpath in deps:
        ext = os.path.splitext(fpath)[1].lower()
        if ext:
            languages[ext] = languages.get(ext, 0) + 1

    layers: dict[str, int] = {}
    for node in graph.nodes():
        layer = _infer_layer(node)
        layers[layer] = layers.get(layer, 0) + 1

    return {
        "deps": deps,
        "graph": graph,
        "changed_funcs": changed_funcs,
        "entry_points": entry_points,
        "dead_nodes": dead_nodes,
        "cycles": cycles,
        "linenos": linenos,
        "complexities": complexities,
        "total_files": total_files,
        "total_functions": total_functions,
        "languages": languages,
        "layers": layers,
    }


def _infer_layer(node: str) -> str:
    if "::" in node:
        fpath = node.split("::")[0]
    else:
        fpath = node
    parts = Path(fpath).parts
    if "test" in parts:
        return "Test"
    if "migration" in parts:
        return "Migration"
    if "config" in parts:
        return "Config"
    if "model" in parts:
        return "Domain"
    if "repository" in parts or "dao" in parts or "store" in parts:
        return "Persistence"
    if "controller" in parts or "route" in parts or "view" in parts:
        return "Presentation"
    if "service" in parts or "use_case" in parts or "command" in parts:
        return "Application"
    return "Utility"


async def analyze_repo(repo_path_str: str) -> dict[str, Any]:
    repo_path = Path(repo_path_str).resolve()
    key = str(repo_path)
    if key in _cache:
        return _cache[key]
    result = await asyncio.to_thread(_analyze_sync, repo_path)
    _cache[key] = result
    return result


def clear_cache(repo_path: str | None = None) -> None:
    if repo_path:
        _cache.pop(str(Path(repo_path).resolve()), None)
    else:
        _cache.clear()
