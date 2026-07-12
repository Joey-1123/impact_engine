from __future__ import annotations

from pathlib import Path
from typing import Any

from core.analyzer import calculate_risk, find_dead_code
from core.detector import find_cycles, find_entry_points
from core.health import (
    HealthFileMetricData,
    HealthFindingData,
    HealthReport,
    Severity,
    attach_impacts,
    score_file,
    compute_kpis,
)
from core.health.biomarkers import BiomarkerResult
from core.summary import build_analysis_summary
from ..progress import ProgressCallback
from ._common import phase_done
import networkx as nx
from datetime import datetime, timezone


def _compute_health_report(
    repo_path: Path,
    graph: nx.DiGraph,
    complexities: dict[str, int],
    entry_points: list[str],
    dead_code: list[str],
) -> HealthReport:
    findings: list[HealthFindingData] = []
    metrics: list[HealthFileMetricData] = []

    for node in graph.nodes():
        func_results: list[BiomarkerResult] = []
        ccn = complexities.get(node, 1)
        nesting = 0

        if ccn > 10:
            func_results.append(
                BiomarkerResult(
                    biomarker_type="complex_method",
                    severity=Severity.HIGH,
                    function_name=node,
                    details={"cyclomatic_complexity": ccn},
                )
            )
        if ccn > 20:
            func_results.append(
                BiomarkerResult(
                    biomarker_type="brain_method",
                    severity=Severity.CRITICAL,
                    function_name=node,
                    details={"cyclomatic_complexity": ccn},
                )
            )

        if func_results:
            scores, deductions = score_file(func_results)
            impacted = attach_impacts(func_results, deductions)
            findings.extend(impacted)
        else:
            scores = {"defect": 10.0, "maintainability": 10.0, "performance": 10.0}

        file_path = node.split("::")[0] if "::" in node else node
        nloc = ccn * 10

        metrics.append(
            HealthFileMetricData(
                file_path=file_path,
                score=scores.get("defect", 10.0) or 10.0,
                max_ccn=ccn,
                max_nesting=nesting,
                nloc=nloc,
                has_test_file=False,
                defect_score=scores.get("defect"),
                maintainability_score=scores.get("maintainability"),
                performance_score=scores.get("performance"),
            )
        )

    hotspot_paths = {
        m.file_path for m in metrics if m.score < 7.0
    }

    kpis = compute_kpis(metrics, hotspot_paths)

    return HealthReport(
        repo_id=str(repo_path),
        analyzed_at=datetime.now(timezone.utc),
        findings=findings,
        metrics=metrics,
        kpis=kpis,
    )


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

    health_report = _compute_health_report(repo_path, graph, complexities, entry_points, list(dead))

    if progress:
        progress.on_message(
            "info",
            f"Health: {len(health_report.findings)} findings across {len(health_report.metrics)} files, "
            f"avg score {health_report.kpis.get('average_health', 'N/A')}",
        )

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
        "health_report": health_report,
    }
