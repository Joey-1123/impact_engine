from __future__ import annotations

from pathlib import Path
from typing import Any

from core.detector import find_cycles, find_entry_points
from ..progress import ProgressCallback
from ._common import phase_done
import networkx as nx


async def run_generation(
    repo_path: Path,
    graph: nx.DiGraph,
    deps: dict[str, list[str]],
    entry_funcs: list[str],
    summary: dict[str, Any],
    *,
    generate_docs: bool = False,
    progress: ProgressCallback | None = None,
    llm_client: Any = None,
) -> dict[str, Any]:
    if progress:
        progress.on_phase_start("generation", None)
        progress.on_message("info", "Generation phase (stub)")

    result: dict[str, Any] = {}

    phase_done(progress, "generation")
    return result
