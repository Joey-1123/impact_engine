from __future__ import annotations

from collections.abc import Callable, Iterable

from .biomarkers import BiomarkerResult
from .models import HealthFileMetricData, HealthFindingData, Severity

CATEGORY_CAPS: dict[str, float] = {
    "organizational": 3.5,
    "structural_complexity": 2.5,
    "test_coverage": 2.0,
    "test_coverage_gradient": 2.0,
    "size_and_complexity": 1.5,
    "duplication": 1.0,
    "test_quality": 0.5,
    "error_handling": 0.5,
}

_SEVERITY_DEDUCTION: dict[Severity, float] = {
    Severity.LOW: 0.3,
    Severity.MEDIUM: 0.7,
    Severity.HIGH: 1.2,
    Severity.CRITICAL: 2.0,
}

_BIOMARKER_WEIGHT_MULTIPLIER: dict[str, float] = {
    "co_change_scatter": 1.8,
    "change_entropy": 1.51,
    "ownership_risk": 1.38,
    "nested_complexity": 1.34,
    "complex_conditional": 1.33,
    "large_method": 1.25,
    "complex_method": 1.21,
    "function_hotspot": 1.16,
    "god_class": 1.13,
    "prior_defect": 1.0,
    "untested_hotspot": 1.3,
    "churn_risk": 1.2,
    "code_age_volatility": 1.1,
    "developer_congestion": 0.5,
    "low_cohesion": 0.5,
    "brain_method": 0.5,
    "bumpy_road": 0.5,
    "primitive_obsession": 0.5,
    "dry_violation": 0.5,
    "knowledge_loss": 0.4,
    "error_handling": 0.5,
}

_BIOMARKER_CATEGORY: dict[str, str] = {
    "brain_method": "structural_complexity",
    "low_cohesion": "structural_complexity",
    "god_class": "structural_complexity",
    "nested_complexity": "structural_complexity",
    "bumpy_road": "structural_complexity",
    "complex_conditional": "structural_complexity",
    "complex_method": "size_and_complexity",
    "large_method": "size_and_complexity",
    "primitive_obsession": "size_and_complexity",
    "dry_violation": "duplication",
    "untested_hotspot": "test_coverage",
    "coverage_gap": "test_coverage",
    "coverage_gradient": "test_coverage_gradient",
    "developer_congestion": "organizational",
    "knowledge_loss": "organizational",
    "hidden_coupling": "organizational",
    "function_hotspot": "organizational",
    "code_age_volatility": "organizational",
    "ownership_risk": "organizational",
    "churn_risk": "organizational",
    "change_entropy": "organizational",
    "co_change_scatter": "organizational",
    "prior_defect": "organizational",
    "large_assertion_block": "test_quality",
    "duplicated_assertion_block": "test_quality",
    "error_handling": "error_handling",
}

DIMENSIONS: tuple[str, ...] = ("defect", "maintainability", "performance")

_BIOMARKER_DIMENSIONS: dict[str, set[str]] = {
    "low_cohesion": {"defect", "maintainability"},
    "brain_method": {"defect", "maintainability"},
    "primitive_obsession": {"defect", "maintainability"},
    "dry_violation": {"defect", "maintainability"},
    "error_handling": {"defect", "maintainability"},
    "god_class": {"defect", "maintainability"},
    "large_method": {"defect", "maintainability"},
    "nested_complexity": {"defect", "maintainability"},
    "io_in_loop": {"performance"},
    "string_concat_in_loop": {"performance"},
    "blocking_sync_in_async": {"performance"},
}

_MAINTAINABILITY_WEIGHT_MULTIPLIER: dict[str, float] = {
    "low_cohesion": 1.0,
    "brain_method": 1.0,
    "primitive_obsession": 1.0,
    "dry_violation": 1.0,
    "error_handling": 1.0,
    "god_class": 1.0,
    "large_method": 1.0,
    "nested_complexity": 1.0,
}

_MAINTAINABILITY_CATEGORY: dict[str, str] = {
    "brain_method": "structural_complexity",
    "low_cohesion": "structural_complexity",
    "god_class": "structural_complexity",
    "nested_complexity": "structural_complexity",
    "large_method": "structural_complexity",
    "primitive_obsession": "size_and_complexity",
    "dry_violation": "duplication",
    "error_handling": "error_handling",
}

_MAINTAINABILITY_CATEGORY_CAPS: dict[str, float] = {
    "structural_complexity": 4.0,
    "size_and_complexity": 2.0,
    "duplication": 2.0,
    "error_handling": 2.0,
}

_MAINTAINABILITY_HOME: frozenset[str] = frozenset({
    "low_cohesion", "brain_method", "primitive_obsession",
    "dry_violation", "error_handling",
})

_PERFORMANCE_WEIGHT_MULTIPLIER: dict[str, float] = {
    "io_in_loop": 1.0,
    "blocking_sync_in_async": 0.7,
    "string_concat_in_loop": 0.7,
}

_PERFORMANCE_CATEGORY: dict[str, str] = {
    "io_in_loop": "performance",
    "string_concat_in_loop": "performance",
    "blocking_sync_in_async": "performance",
}

_PERFORMANCE_CATEGORY_CAPS: dict[str, float] = {
    "performance": 1.0,
}

_PERFORMANCE_HOME: frozenset[str] = frozenset({
    "io_in_loop", "string_concat_in_loop", "blocking_sync_in_async",
})


def severity_deduction(sev: Severity) -> float:
    return _SEVERITY_DEDUCTION.get(sev, 0.5)


def biomarker_weight(name: str) -> float:
    return _BIOMARKER_WEIGHT_MULTIPLIER.get(name, 1.0)


def biomarker_category(name: str) -> str:
    return _BIOMARKER_CATEGORY.get(name, "size_and_complexity")


def dimensions_for(name: str) -> set[str]:
    return _BIOMARKER_DIMENSIONS.get(name, {"defect"})


def biomarker_dimension(name: str) -> str:
    if name in _PERFORMANCE_HOME:
        return "performance"
    if name in _MAINTAINABILITY_HOME:
        return "maintainability"
    return "defect"


def maintainability_weight(name: str) -> float:
    return _MAINTAINABILITY_WEIGHT_MULTIPLIER.get(name, 1.0)


def maintainability_category(name: str) -> str:
    return _MAINTAINABILITY_CATEGORY.get(name, "size_and_complexity")


def performance_weight(name: str) -> float:
    return _PERFORMANCE_WEIGHT_MULTIPLIER.get(name, 1.0)


def performance_category(name: str) -> str:
    return _PERFORMANCE_CATEGORY.get(name, "performance")


def _score_dimension(
    results_list: list[BiomarkerResult],
    weight_fn: Callable[[str], float],
    category_fn: Callable[[str], str],
    caps: dict[str, float],
) -> tuple[float, list[float]]:
    raw: dict[str, list[tuple[int, float]]] = {}
    for idx, r in enumerate(results_list):
        cat = category_fn(r.biomarker_type)
        base = r.deduction if r.deduction is not None else severity_deduction(r.severity)
        weighted = base * weight_fn(r.biomarker_type)
        raw.setdefault(cat, []).append((idx, weighted))

    per_result = [0.0] * len(results_list)
    total = 0.0
    for cat, entries in raw.items():
        cap = caps.get(cat, 1.0)
        cat_sum = sum(d for _, d in entries)
        if cat_sum <= cap:
            for idx, d in entries:
                per_result[idx] = d
            total += cat_sum
        else:
            scale = cap / cat_sum if cat_sum > 0 else 0.0
            for idx, d in entries:
                per_result[idx] = d * scale
            total += cap

    score = max(1.0, min(10.0, 10.0 - total))
    return score, per_result


def score_file(results: Iterable[BiomarkerResult]) -> tuple[dict[str, float | None], list[float]]:
    results_list = list(results)

    defect_idx = [
        i for i, r in enumerate(results_list) if "defect" in dimensions_for(r.biomarker_type)
    ]
    defect_results = [results_list[i] for i in defect_idx]
    defect_score, defect_sub = _score_dimension(
        defect_results, biomarker_weight, biomarker_category, CATEGORY_CAPS
    )
    defect_deductions = [0.0] * len(results_list)
    for sub_i, orig_i in enumerate(defect_idx):
        defect_deductions[orig_i] = defect_sub[sub_i]

    maint_results = [
        r for r in results_list if "maintainability" in dimensions_for(r.biomarker_type)
    ]
    maint_score, _ = _score_dimension(
        maint_results,
        maintainability_weight,
        maintainability_category,
        _MAINTAINABILITY_CATEGORY_CAPS,
    )

    perf_results = [
        r for r in results_list if "performance" in dimensions_for(r.biomarker_type)
    ]
    perf_score, _ = _score_dimension(
        perf_results,
        performance_weight,
        performance_category,
        _PERFORMANCE_CATEGORY_CAPS,
    )

    scores: dict[str, float | None] = {
        "defect": defect_score,
        "maintainability": maint_score,
        "performance": perf_score,
    }
    return scores, defect_deductions


def attach_impacts(
    results: list[BiomarkerResult], deductions: list[float]
) -> list[HealthFindingData]:
    out: list[HealthFindingData] = []
    for r, d in zip(results, deductions, strict=True):
        out.append(
            HealthFindingData(
                biomarker_type=r.biomarker_type,
                severity=r.severity,
                file_path="",
                function_name=r.function_name,
                line_start=r.line_start,
                line_end=r.line_end,
                details=r.details,
                health_impact=round(d, 3),
                reason=r.reason,
                dimension=biomarker_dimension(r.biomarker_type),
            )
        )
    return out


def compute_kpis(
    metrics: list[HealthFileMetricData],
    hotspot_paths: set[str],
) -> dict[str, object]:
    if not metrics:
        return {
            "hotspot_health": 10.0,
            "average_health": 10.0,
            "worst_performer_path": None,
            "worst_performer_score": None,
            "file_count": 0,
        }

    def _wavg(rows: list[HealthFileMetricData]) -> float:
        if not rows:
            return 10.0
        total_w = sum(max(r.nloc, 1) for r in rows)
        if total_w == 0:
            return sum(r.score for r in rows) / len(rows)
        return sum(r.score * max(r.nloc, 1) for r in rows) / total_w

    hotspots = [m for m in metrics if m.file_path in hotspot_paths]
    worst = min(metrics, key=lambda m: m.score)

    return {
        "hotspot_health": round(_wavg(hotspots), 2),
        "average_health": round(_wavg(metrics), 2),
        "worst_performer_path": worst.file_path,
        "worst_performer_score": round(worst.score, 2),
        "file_count": len(metrics),
    }
