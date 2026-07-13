from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from core.health.biomarkers._models import FileContext, BiomarkerResult, Severity


_IMPORT_NAMES: dict[str, str] = {"csv", "json", "pickle", "yaml", "toml", "xml"}


def _parse_python(file_path: str) -> ast.AST | None:
    try:
        return ast.parse(Path(file_path).read_text(encoding="utf-8"))
    except SyntaxError:
        return None


def _get_function_name(node: ast.AST) -> str:
    return getattr(node, "name", "")


def _count_if_nested(node: ast.AST, target_types: tuple[type, ...]) -> int:
    count = 0
    for child in ast.walk(node):
        if isinstance(child, target_types):
            count += 1
    return count


def _max_nesting(node: ast.AST) -> int:
    max_depth = 0

    def walk(n: ast.AST, depth: int) -> None:
        nonlocal max_depth
        if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.AsyncFor, ast.With, ast.AsyncWith)):
            depth += 1
            max_depth = max(max_depth, depth)
        for child in ast.iter_child_nodes(n):
            walk(child, depth)

    walk(node, 0)
    return max_depth


def _collect_functions(tree: ast.AST) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    funcs: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append((node.name, node))
    return funcs


def _collect_classes(tree: ast.AST) -> list[ast.ClassDef]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]


def _ccn(node: ast.AST) -> int:
    count = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Assert)):
            count += 1
        elif isinstance(child, ast.BoolOp):
            count += len(child.values) - 1
        elif isinstance(child, ast.Try):
            count += len(child.handlers)
    return count


def _count_variables(node: ast.FunctionDef) -> int:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            names.add(child.id)
    return len(names)


def _count_conditionals(node: ast.FunctionDef) -> int:
    return _count_if_nested(node, (ast.If,))


def _loc(node: ast.FunctionDef) -> int:
    return max(getattr(node, "end_lineno", 1) - getattr(node, "lineno", 1), 0)
