from __future__ import annotations

from typing import Any

from core.health.biomarkers._models import FileContext, BiomarkerResult, Severity


def detect_untested_hotspot(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    if not ctx.has_test_file and ctx.dependents_count > 5:
        results.append(BiomarkerResult(
            biomarker_type="untested_hotspot",
            severity=Severity.HIGH,
            details={"dependents": ctx.dependents_count},
            reason=f"No test file for hotspot ({ctx.dependents_count} dependents)",
        ))
    return results


def detect_coverage_gap(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    if not ctx.has_test_file and ctx.nloc > 100:
        results.append(BiomarkerResult(
            biomarker_type="coverage_gap",
            severity=Severity.MEDIUM,
            details={"nloc": ctx.nloc},
            reason=f"No test coverage for {ctx.nloc} LOC file",
        ))
    return results


def detect_function_hotspot(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    if ctx.pagerank_score > 0.01 and ctx.dependents_count > 10:
        results.append(BiomarkerResult(
            biomarker_type="function_hotspot",
            severity=Severity.MEDIUM,
            details={"pagerank": round(ctx.pagerank_score, 4), "dependents": ctx.dependents_count},
            reason=f"Central function (PageRank={ctx.pagerank_score:.4f}, {ctx.dependents_count} dependents)",
        ))
    return results


def detect_ownership_risk(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    owners = ctx.git_meta.get("owners", [])
    if len(owners) == 1 and ctx.nloc > 200:
        results.append(BiomarkerResult(
            biomarker_type="ownership_risk",
            severity=Severity.MEDIUM,
            details={"owners": len(owners), "nloc": ctx.nloc},
            reason=f"Single owner for {ctx.nloc} LOC file",
        ))
    return results


def detect_developer_congestion(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    devs = ctx.git_meta.get("authors", [])
    recent_changes = ctx.git_meta.get("recent_changes", 0)
    if len(devs) >= 3 and recent_changes > 10:
        results.append(BiomarkerResult(
            biomarker_type="developer_congestion",
            severity=Severity.LOW,
            details={"developers": len(devs), "changes": recent_changes},
            reason=f"Multiple developers ({len(devs)}) on high-churn file",
        ))
    return results


def detect_knowledge_loss(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    former_owners = ctx.git_meta.get("former_owners", 0)
    if former_owners > 2:
        results.append(BiomarkerResult(
            biomarker_type="knowledge_loss",
            severity=Severity.LOW,
            details={"former_owners": former_owners},
            reason=f"{former_owners} former owners no longer active",
        ))
    return results


def detect_churn_risk(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    changes = ctx.git_meta.get("recent_changes", 0)
    if changes > 15:
        results.append(BiomarkerResult(
            biomarker_type="churn_risk",
            severity=Severity.MEDIUM,
            details={"recent_changes": changes},
            reason=f"High churn: {changes} recent changes",
        ))
    return results


def detect_code_age_volatility(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    age_days = ctx.git_meta.get("age_days", 0)
    recent_changes = ctx.git_meta.get("recent_changes", 0)
    if age_days > 365 and recent_changes > 5:
        results.append(BiomarkerResult(
            biomarker_type="code_age_volatility",
            severity=Severity.LOW,
            details={"age_days": age_days, "recent_changes": recent_changes},
            reason=f"Old file ({age_days}d old) with recent churn",
        ))
    return results


def detect_change_entropy(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    entropy = ctx.git_meta.get("change_entropy", 0.0)
    if entropy > 0.7:
        results.append(BiomarkerResult(
            biomarker_type="change_entropy",
            severity=Severity.MEDIUM,
            details={"entropy": round(entropy, 3)},
            reason=f"High change entropy: {entropy:.2f}",
        ))
    return results


def detect_co_change_scatter(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    co_changes = ctx.git_meta.get("co_change_partners", 0)
    if co_changes > 5:
        results.append(BiomarkerResult(
            biomarker_type="co_change_scatter",
            severity=Severity.LOW,
            details={"co_change_partners": co_changes},
            reason=f"Frequent co-change with {co_changes} files",
        ))
    return results


def detect_prior_defect(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    bug_fixes = ctx.git_meta.get("bug_fixes", 0)
    if bug_fixes > 3:
        results.append(BiomarkerResult(
            biomarker_type="prior_defect",
            severity=Severity.MEDIUM if bug_fixes > 5 else Severity.LOW,
            details={"bug_fixes": bug_fixes},
            reason=f"{bug_fixes} prior bug fixes",
        ))
    return results
