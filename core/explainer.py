# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from typing import List, Dict, Any, Set
import networkx as nx


def explain_impact(graph: nx.DiGraph, start_node: str, impacted_nodes: Set[str]) -> Dict[str, Any]:
    explanations: List[Dict[str, Any]] = []

    total_impact = len(impacted_nodes)

    reversed_graph = graph.reverse()
    try:
        paths = nx.single_source_shortest_path(reversed_graph, start_node)
    except nx.NetworkXNoPath:
        paths = {}

    for target in impacted_nodes:
        if target == start_node:
            continue

        path = paths.get(target)
        if path and len(path) >= 2:
            direct = len(path) == 2

            if direct:
                reason = f"{target} directly depends on {start_node}"
            else:
                via = " → ".join(path[1:-1])
                reason = f"{target} depends on {start_node} via {via}"

            explanations.append({
                "target": target,
                "path": list(path),
                "reason": reason,
                "depth": len(path) - 1
            })

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
