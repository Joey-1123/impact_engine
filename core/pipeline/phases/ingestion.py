from __future__ import annotations

from pathlib import Path
from typing import Any

from core.extractor import extract_project_dependencies_rich
from core.file_loader import get_python_files
from core.graph_builder import build_graph
from ..progress import ProgressCallback
from ._common import phase_done


async def run_ingestion(
    repo_path: Path,
    *,
    respect_gitignore: bool = True,
    use_cache: bool = True,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    if progress:
        progress.on_phase_start("ingestion", None)
        progress.on_message("info", "Discovering files...")

    files = get_python_files(str(repo_path), respect_gitignore=respect_gitignore)

    if progress:
        progress.on_message("info", f"Found {len(files)} Python files")
        progress.on_phase_start("parse", len(files))

    deps, linenos, complexities = extract_project_dependencies_rich(
        str(repo_path), respect_gitignore=respect_gitignore
    )
    entry_funcs: list[str] = []

    if progress:
        progress.on_message("info", f"Extracted {len(deps)} modules")
        progress.on_phase_start("graph", None)

    graph = build_graph(deps)

    if progress:
        progress.on_message(
            "info",
            f"Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges",
        )

    phase_done(progress, "ingestion")

    return {
        "deps": deps,
        "entry_funcs": entry_funcs,
        "linenos": linenos,
        "complexities": complexities,
        "graph": graph,
    }
