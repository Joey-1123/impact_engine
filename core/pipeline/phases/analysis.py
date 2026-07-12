from __future__ import annotations

from pathlib import Path
from typing import Any

from core.analyzer import calculate_risk, find_dead_code
from core.detector import find_cycles, find_entry_points
from core.summary import build_analysis_summary
from ..progress import ProgressCallback
from ._common import phase_done
import networkx as nx


async def run_analysis(
    repo_path: Path,
    graph: nx.DiGraph,
    deps: dict[str, list[str]],
    entry_funcs: list[str],
    linenos: dict[str, int],
    complexities: dict[str, int],
    *,
    changed_funcs: list[str] | None = None,
    limit: int = 10,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    if progress:
        progress.on_phase_start("analysis", None)

    entry_points = find_entry_points(graph, entry_funcs)

    dead = find_dead_code(graph, entry_points)

    if progress:
        progress.on_message("info", f"Dead code: {len(dead)} nodes")
        progress.on_phase_start("health", None)

    cycles = find_cycles(graph)

    if progress:
        progress.on_message("info", f"Cycles: {len(cycles)} detected")

    summary = build_analysis_summary(
        graph,
        changed_nodes=set(changed_funcs) if changed_funcs else None,
        dead_nodes=list(dead),
        limit=limit,
        complexities=complexities,
    )

    phase_done(progress, "analysis")

    return {
        "entry_points": entry_points,
        "dead_code": dead,
        "cycles": cycles,
        "summary": summary,
    }
