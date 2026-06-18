# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import subprocess
import sys
from typing import Dict, Optional
from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.git_analyzer import get_changed_functions
from core.analyzer import calculate_risk
from core.detector import find_entry_points


def _git_merge_base(ref_a: str, ref_b: str, cwd: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "merge-base", ref_a, ref_b],
            capture_output=True, text=True, encoding="utf-8", cwd=cwd,
            timeout=60,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Failed to get merge base: {e}", file=sys.stderr)
    return None


def compare_branches(
    project_path: str,
    base_ref: str = "main",
    head_ref: Optional[str] = None,
) -> Dict:
    if head_ref is None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, encoding="utf-8", cwd=project_path,
                timeout=60,
            )
            head_ref = result.stdout.strip() if result.returncode == 0 else "HEAD"
        except Exception as e:
            print(f"Failed to resolve HEAD ref: {e}", file=sys.stderr)
            head_ref = "HEAD"

    merge_base = _git_merge_base(base_ref, head_ref, project_path)

    if not merge_base:
        return {"error": f"Could not find merge base between {base_ref} and {head_ref}"}

    deps = extract_project_dependencies(project_path)
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
