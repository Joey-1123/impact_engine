from __future__ import annotations

import ast
from typing import Any

from core.health.biomarkers._models import FileContext, BiomarkerResult, Severity
from core.health.biomarkers._base import _parse_python, _collect_functions


def detect_io_in_loop(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []

    io_calls = {"open", "read", "write", "readline", "readlines", "writelines", "close"}

    for name, node in _collect_functions(tree):
        for child in ast.walk(node):
            if not isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
                continue
            for sub in ast.walk(child):
                if isinstance(sub, ast.Call):
                    fn = sub.func
                    if isinstance(fn, ast.Attribute) and fn.attr in io_calls:
                        results.append(BiomarkerResult(
                            biomarker_type="io_in_loop",
                            severity=Severity.MEDIUM,
                            function_name=name,
                            line_start=child.lineno,
                            line_end=child.end_lineno,
                            details={"io_call": fn.attr},
                            reason=f"IO call '{fn.attr}' inside loop",
                        ))
                    elif isinstance(fn, ast.Name) and fn.id in io_calls:
                        results.append(BiomarkerResult(
                            biomarker_type="io_in_loop",
                            severity=Severity.MEDIUM,
                            function_name=name,
                            line_start=child.lineno,
                            line_end=child.end_lineno,
                            details={"io_call": fn.id},
                            reason=f"IO call '{fn.id}' inside loop",
                        ))
    return results


def detect_string_concat_in_loop(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []

    for name, node in _collect_functions(tree):
        for child in ast.walk(node):
            if not isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
                continue
            augassign_count = 0
            binop_count = 0
            for sub in ast.walk(child):
                if isinstance(sub, ast.AugAssign) and isinstance(sub.op, ast.Add):
                    augassign_count += 1
                elif isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Add):
                    if isinstance(sub.left, ast.Constant) and isinstance(sub.left.value, str):
                        binop_count += 1
                    elif isinstance(sub.right, ast.Constant) and isinstance(sub.right.value, str):
                        binop_count += 1
            if augassign_count > 2 or binop_count > 3:
                results.append(BiomarkerResult(
                    biomarker_type="string_concat_in_loop",
                    severity=Severity.LOW,
                    function_name=name,
                    line_start=child.lineno,
                    line_end=child.end_lineno,
                    details={"aug_assign": augassign_count, "binop": binop_count},
                    reason="String concatenation inside loop",
                ))
    return results


def detect_blocking_sync_in_async(ctx: FileContext) -> list[BiomarkerResult]:
    tree = _parse_python(ctx.file_path)
    if tree is None:
        return []
    results: list[BiomarkerResult] = []

    blocking_imports = {"time.sleep", "subprocess.run", "subprocess.call", "os.system", "os.popen", "requests.get", "requests.post"}

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                fn = child.func
                if isinstance(fn, ast.Attribute):
                    import ast as _ast  # noqa: F811
                    call_str = f"{fn.value.id}.{fn.attr}" if isinstance(fn.value, ast.Name) else ""
                    if call_str in blocking_imports:
                        results.append(BiomarkerResult(
                            biomarker_type="blocking_sync_in_async",
                            severity=Severity.HIGH,
                            function_name=node.name,
                            line_start=child.lineno,
                            line_end=child.end_lineno,
                            details={"call": call_str},
                            reason=f"Blocking call '{call_str}' in async function",
                        ))
    return results
