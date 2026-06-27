# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import shlex
import subprocess
import sys
from typing import Dict, Optional
from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.git_analyzer import get_changed_functions, get_current_branch, get_merge_base
from core.analyzer import calculate_risk
from core.detector import find_entry_points


def compare_branches(
    project_path: str,
    base_ref: str = "main",
    head_ref: Optional[str] = None,
    respect_gitignore: bool = True,
) -> Dict:
    if head_ref is None:
        head_ref = get_current_branch(cwd=project_path)

    merge_base = get_merge_base(base_ref, head_ref, project_path)

    if not merge_base:
        return {"error": f"Could not find merge base between {base_ref} and {head_ref}"}

    deps = extract_project_dependencies(project_path, respect_gitignore=respect_gitignore)
    if not deps:
        return {"error": "No Python files found"}

    graph = build_graph(deps)

    base_changed = set(get_changed_functions(deps, ref=f"{merge_base}...{base_ref}", cwd=project_path))
    head_changed = set(get_changed_functions(deps, ref=f"{merge_base}...{head_ref}", cwd=project_path))

    new_changes = head_changed - base_changed
    resolved = base_changed - head_changed
    still_changed = head_changed & base_changed

    entry_points = find_entry_points(graph)

    new_risks = {}
    for func in new_changes:
        risk = calculate_risk(graph, func)
        new_risks[func] = risk

    still_risks = {}
    for func in still_changed:
        risk = calculate_risk(graph, func)
        still_risks[func] = risk

    total_base_risk = sum(calculate_risk(graph, f) for f in base_changed)
    total_head_risk = sum(calculate_risk(graph, f) for f in head_changed)

    return {
        "base_ref": base_ref,
        "head_ref": head_ref,
        "merge_base": merge_base,
        "summary": {
            "new_changes": len(new_changes),
            "resolved": len(resolved),
            "still_changed": len(still_changed),
            "total_on_base": len(base_changed),
            "total_on_head": len(head_changed),
        },
        "risk_delta": total_head_risk - total_base_risk,
        "new_risks": {k: v for k, v in sorted(new_risks.items(), key=lambda x: -x[1])},
        "still_risks": {k: v for k, v in sorted(still_risks.items(), key=lambda x: -x[1])},
        "new_changes": sorted(new_changes),
        "resolved_changes": sorted(resolved),
    }
