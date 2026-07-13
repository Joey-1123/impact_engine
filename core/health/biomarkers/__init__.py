from __future__ import annotations

import os
from typing import Any

from core.health.biomarkers._models import FileContext, BiomarkerResult
from core.health.biomarkers.structural import (
    detect_brain_method,
    detect_god_class,
    detect_complex_method,
    detect_large_method,
    detect_nested_complexity,
    detect_primitive_obsession,
    detect_complex_conditional,
    detect_low_cohesion,
    detect_bumpy_road,
    detect_large_class,
    detect_dry_violation,
    detect_error_handling,
)
from core.health.biomarkers.performance import (
    detect_io_in_loop,
    detect_string_concat_in_loop,
    detect_blocking_sync_in_async,
)
from core.health.biomarkers.organizational import (
    detect_untested_hotspot,
    detect_coverage_gap,
    detect_function_hotspot,
    detect_ownership_risk,
    detect_developer_congestion,
    detect_knowledge_loss,
    detect_churn_risk,
    detect_code_age_volatility,
    detect_change_entropy,
    detect_co_change_scatter,
    detect_prior_defect,
)

_BIOMARKER_FNS: list[Any] = [
    detect_brain_method,
    detect_god_class,
    detect_complex_method,
    detect_large_method,
    detect_nested_complexity,
    detect_primitive_obsession,
    detect_complex_conditional,
    detect_low_cohesion,
    detect_bumpy_road,
    detect_large_class,
    detect_dry_violation,
    detect_error_handling,
    detect_io_in_loop,
    detect_string_concat_in_loop,
    detect_blocking_sync_in_async,
    detect_untested_hotspot,
    detect_coverage_gap,
    detect_function_hotspot,
    detect_ownership_risk,
    detect_developer_congestion,
    detect_knowledge_loss,
    detect_churn_risk,
    detect_code_age_volatility,
    detect_change_entropy,
    detect_co_change_scatter,
    detect_prior_defect,
]


def run_all_biomarkers(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    for fn in _BIOMARKER_FNS:
        try:
            results.extend(fn(ctx))
        except Exception:
            pass
    return results


def analyze_file(
    file_path: str,
    *,
    nloc: int = 0,
    has_test_file: bool = False,
    module: str | None = None,
    dependents_count: int = 0,
    pagerank_score: float = 0.0,
    function_metrics: dict[str, Any] | None = None,
    class_metrics: list[Any] | None = None,
    git_meta: dict[str, Any] | None = None,
    clones: list[Any] | None = None,
    duplication_pct: float | None = None,
) -> list[BiomarkerResult]:
    lang = "python"
    if file_path.endswith(".py"):
        lang = "python"
    elif file_path.endswith((".js", ".ts", ".tsx")):
        lang = "javascript"

    ctx = FileContext(
        file_path=file_path,
        language=lang,
        nloc=nloc,
        has_test_file=has_test_file,
        module=module,
        function_metrics=function_metrics or {},
        class_metrics=class_metrics or [],
        git_meta=git_meta or {},
        dependents_count=dependents_count,
        pagerank_score=pagerank_score,
        clones=clones or [],
        duplication_pct=duplication_pct,
    )
    return run_all_biomarkers(ctx)
