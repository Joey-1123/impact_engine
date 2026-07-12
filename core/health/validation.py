from __future__ import annotations

from typing import Any


def compute_defect_accuracy(
    metrics: list[Any],
    findings: list[Any],
    prior_defect_paths: set[str],
) -> dict[str, Any]:
    scored_paths = {m.file_path for m in metrics}
    if not scored_paths:
        return {"precision_at_k": {}, "recall": 0.0, "total_defect_files": 0}

    hotspot_paths = {
        m.file_path for m in metrics
        if hasattr(m, 'score') and m.score is not None and m.score < 7.0
    }

    true_positives = len(hotspot_paths & prior_defect_paths)
    false_positives = len(hotspot_paths - prior_defect_paths)
    false_negatives = len(prior_defect_paths - hotspot_paths)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0

    k_values = [5, 10, 25]
    precision_at_k = {}
    for k in k_values:
        top_k = sorted(metrics, key=lambda m: getattr(m, 'score', 10) or 10)[:k]
        top_k_defects = sum(1 for m in top_k if m.file_path in prior_defect_paths)
        precision_at_k[f"p@{k}"] = round(top_k_defects / k, 3)

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(2 * precision * recall / (precision + recall), 3) if (precision + recall) > 0 else 0.0,
        "precision_at_k": precision_at_k,
        "total_defect_files": len(prior_defect_paths),
    }
