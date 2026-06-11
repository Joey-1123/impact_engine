# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from typing import List, Dict, Any, Set
from networkx.exception import NetworkXNoPath
from networkx.algorithms.shortest_paths import shortest_path


def explain_impact(graph, start_node: str, impacted_nodes: Set[str]) -> Dict[str, Any]:
    explanations: List[Dict[str, Any]] = []

    total_impact = len(impacted_nodes)

    for target in impacted_nodes:
        if target == start_node:
            continue

        try:
            path = list(shortest_path(graph, target, start_node))

            if len(path) >= 2:
                direct = len(path) == 2

                if direct:
                    reason = f"{target} directly depends on {start_node}"
                else:
                    via = " → ".join(path[1:-1])
                    reason = f"{target} depends on {start_node} via {via}"

                explanations.append({
                    "target": target,
                    "path": path,
                    "reason": reason,
                    "depth": len(path) - 1
                })

        except NetworkXNoPath:
            continue

    if total_impact >= 5:
        severity = "HIGH"
        summary = f"High risk: impacts {total_impact} downstream functions."
    elif total_impact >= 3:
        severity = "MEDIUM"
        summary = f"Moderate risk: impacts {total_impact} functions."
    else:
        severity = "LOW"
        summary = f"Low risk: limited impact ({total_impact} functions)."

    return {
        "summary": summary,
        "severity": severity,
        "details": explanations
    }
