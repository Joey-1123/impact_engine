# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import json
from typing import Dict, List, Set
import networkx as nx


def export_mermaid(graph: nx.DiGraph) -> str:
    lines = ["graph TD"]
    for u, v in graph.edges():
        u_label = u.split("::")[-1].replace("(", "_").replace(")", "_").replace("-", "_")
        v_label = v.split("::")[-1].replace("(", "_").replace(")", "_").replace("-", "_")
        lines.append(f'    {u_label}["{u.split("::")[-1]}"] --> {v_label}["{v.split("::")[-1]}"]')
    return "\n".join(lines)


def export_mermaid_with_changes(graph: nx.DiGraph, changed_nodes: Set[str] = None) -> str:
    changed_set = set(changed_nodes or [])
    lines = ["graph TD"]
    for u, v in graph.edges():
        u_label = u.split("::")[-1].replace("(", "_").replace(")", "_").replace("-", "_")
        v_label = v.split("::")[-1].replace("(", "_").replace(")", "_").replace("-", "_")
        lines.append(f'    {u_label}["{u.split("::")[-1]}"] --> {v_label}["{v.split("::")[-1]}"]')
    if changed_set:
        changed_ids = [
            n.split("::")[-1].replace("(", "_").replace(")", "_").replace("-", "_")
            for n in changed_set
        ]
        for cid in changed_ids:
            lines.append(f"    class {cid} changed;")
        lines.append("    classDef changed fill:#ff6666,stroke:#333,stroke-width:2px;")
    return "\n".join(lines)


def export_sarif(
    graph: nx.DiGraph,
    changed_nodes: List[str] = None,
    dead_nodes: List[str] = None,
    tool_name: str = "impact-engine",
    tool_version: str = "0.3.0",
) -> str:
    changed_set = set(changed_nodes or [])
    dead_set = set(dead_nodes or [])

    results = []

    for node in graph.nodes():
        func_name = node.split("::")[-1]
        file_path = node.split("::")[0]

        risk = 0
        if node in changed_set:
            risk = graph.out_degree(node)

        if risk > 0 or node in dead_set:
            level = "error" if risk >= 5 else "warning"

            if node in dead_set:
                message_text = f"Dead function: {func_name} (unreachable)"
            else:
                message_text = f"High impact function: {func_name} (risk={risk})"

            result = {
                "ruleId": "impact-engine/dead-code" if node in dead_set else "impact-engine/high-risk",
                "level": level,
                "message": {"text": message_text},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": file_path},
                            "region": {"startLine": 1},
                        }
                    }
                ],
            }
            results.append(result)

    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": tool_version,
                        "rules": [
                            {
                                "id": "impact-engine/dead-code",
                                "name": "Dead Code",
                                "shortDescription": {"text": "Dead code detection"},
                                "fullDescription": {"text": "Functions unreachable from entry points"},
                                "defaultConfiguration": {"level": "warning"},
                            },
                            {
                                "id": "impact-engine/high-risk",
                                "name": "High Risk",
                                "shortDescription": {"text": "High impact risk"},
                                "fullDescription": {"text": "Functions with high blast radius risk score"},
                                "defaultConfiguration": {"level": "error"},
                            },
                        ],
                    }
                },
                "results": results,
            }
        ],
    }

    return json.dumps(sarif, indent=2)
