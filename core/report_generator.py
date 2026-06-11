# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from typing import List, Dict, Any


def generate_pr_report(changed_funcs: List[str], impact_data: List[Dict[str, Any]]) -> str:
    report: List[str] = []

    total_changed = len(changed_funcs)
    total_impacted = sum(len(item["impact"]) for item in impact_data)

    if total_impacted >= 5:
        overall_risk = "HIGH"
    elif total_impacted >= 3:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    report.append("=== IMPACT ANALYSIS REPORT ===\n")

    report.append(f"Changed Functions: {total_changed}")
    report.append(f"Total Impacted Functions: {total_impacted}")
    report.append(f"Overall Risk: {overall_risk}\n")

    for item in impact_data:
        report.append(f"\nFunction: {item['function']}")
        report.append(f"Risk Score: {item['risk']}")

        report.append("Impacts:")
        for i in item["impact"]:
            report.append(f"  - {i}")

        report.append("Why:")
        for e in item["explanation"]["details"]:
            report.append(f"  • {e['reason']}")

    return "\n".join(report)
