from __future__ import annotations

import ast
from typing import Any

from core.health.biomarkers._models import FileContext, BiomarkerResult, Severity
from core.health.biomarkers._base import (
    _parse_python,
    _collect_functions,
    _collect_classes,
    _ccn,
    _max_nesting,
    _loc,
    _count_variables,
    _count_conditionals,
    _get_function_name,
)


def detect_brain_method(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []
    for name, node in _collect_functions(tree):
        c = _ccn(node)
        v = _count_variables(node)
        cd = _count_conditionals(node)
        if c >= 15 and v >= 15 and cd >= 5:
            results.append(BiomarkerResult(
                biomarker_type="brain_method",
                severity=Severity.HIGH,
                function_name=name,
                line_start=node.lineno,
                line_end=node.end_lineno,
                details={"ccn": c, "variables": v, "conditionals": cd},
                reason=f"Brain method: CCN={c}, variables={v}, conditionals={cd}",
            ))
    return results


def detect_god_class(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []
    for cls in _collect_classes(tree):
        methods = [n for n in ast.walk(cls) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        attributes = [n for n in ast.walk(cls) if isinstance(n, ast.Assign)]
        if len(methods) > 15 and len(attributes) > 20:
            results.append(BiomarkerResult(
                biomarker_type="god_class",
                severity=Severity.MEDIUM,
                function_name=cls.name,
                line_start=cls.lineno,
                line_end=cls.end_lineno,
                details={"methods": len(methods), "attributes": len(attributes)},
                reason=f"God class: {len(methods)} methods, {len(attributes)} attributes",
            ))
    return results


def detect_complex_method(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []
    for name, node in _collect_functions(tree):
        c = _ccn(node)
        if c > 10:
            sev = Severity.HIGH if c > 20 else Severity.MEDIUM
            results.append(BiomarkerResult(
                biomarker_type="complex_method",
                severity=sev,
                function_name=name,
                line_start=node.lineno,
                line_end=node.end_lineno,
                details={"ccn": c},
                reason=f"High cyclomatic complexity: {c}",
            ))
    return results


def detect_large_method(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []
    for name, node in _collect_functions(tree):
        length = _loc(node)
        if length > 60:
            sev = Severity.HIGH if length > 100 else Severity.MEDIUM
            results.append(BiomarkerResult(
                biomarker_type="large_method",
                severity=sev,
                function_name=name,
                line_start=node.lineno,
                line_end=node.end_lineno,
                details={"loc": length},
                reason=f"Large method: {length} lines",
            ))
    return results


def detect_nested_complexity(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []
    for name, node in _collect_functions(tree):
        depth = _max_nesting(node)
        if depth > 4:
            sev = Severity.HIGH if depth > 6 else Severity.MEDIUM
            results.append(BiomarkerResult(
                biomarker_type="nested_complexity",
                severity=sev,
                function_name=name,
                line_start=node.lineno,
                line_end=node.end_lineno,
                details={"max_nesting": depth},
                reason=f"Deep nesting: {depth} levels",
            ))
    return results


def detect_primitive_obsession(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []
    for name, node in _collect_functions(tree):
        primitives = 0
        for child in ast.walk(node):
            if isinstance(child, ast.arg) and child.arg not in ("self", "cls", "mcs"):
                primitives += 1
        if primitives > 5:
            results.append(BiomarkerResult(
                biomarker_type="primitive_obsession",
                severity=Severity.LOW,
                function_name=name,
                line_start=node.lineno,
                line_end=node.end_lineno,
                details={"primitive_params": primitives},
                reason=f"Many primitive parameters: {primitives}",
            ))
    return results


def detect_complex_conditional(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []
    for name, node in _collect_functions(tree):
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                parts = 0
                for sub in ast.walk(child.test):
                    if isinstance(sub, ast.BoolOp):
                        parts += len(sub.values) - 1
                    if isinstance(sub, ast.Compare):
                        parts += 1
                if parts > 5:
                    results.append(BiomarkerResult(
                        biomarker_type="complex_conditional",
                        severity=Severity.MEDIUM,
                        function_name=name,
                        line_start=child.lineno,
                        line_end=child.end_lineno,
                        details={"parts": parts},
                        reason=f"Complex conditional: {parts} sub-expressions",
                    ))
    return results


def detect_low_cohesion(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []
    for cls in _collect_classes(tree):
        methods = [n for n in ast.walk(cls) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        attrs_in_methods: set[str] = set()
        body_attrs: set[str] = set()
        for n in ast.walk(cls):
            if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store):
                if isinstance(n.value, ast.Name) and n.value.id == "self":
                    body_attrs.add(n.attr)
        for m in methods:
            for n in ast.walk(m):
                if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Load):
                    if isinstance(n.value, ast.Name) and n.value.id == "self":
                        attrs_in_methods.add(n.attr)
        if not body_attrs:
            continue
        cohesion = len(attrs_in_methods & body_attrs) / len(body_attrs) if body_attrs else 1.0
        if cohesion < 0.3 and len(body_attrs) > 3:
            results.append(BiomarkerResult(
                biomarker_type="low_cohesion",
                severity=Severity.MEDIUM,
                function_name=cls.name,
                line_start=cls.lineno,
                line_end=cls.end_lineno,
                details={"cohesion_ratio": round(cohesion, 2), "attributes": len(body_attrs)},
                reason=f"Low cohesion: {cohesion:.0%} attribute usage",
            ))
    return results


def detect_bumpy_road(ctx: FileContext) -> list[BiomarkerResult]:
    results: list[BiomarkerResult] = []
    changelog = ctx.git_meta.get("recent_changes", 0)
    ccn = ctx.function_metrics.get("ccn", 0)
    if changelog > 5 and ccn > 8:
        results.append(BiomarkerResult(
            biomarker_type="bumpy_road",
            severity=Severity.MEDIUM,
            details={"recent_changes": changelog, "ccn": ccn},
            reason=f"High churn ({changelog}) + high complexity ({ccn})",
        ))
    return results
