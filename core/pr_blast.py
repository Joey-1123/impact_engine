from __future__ import annotations

import math
import os
from typing import Any

import networkx as nx


def score_file(
    file_path: str,
    pagerank_score: float = 0.0,
    temporal_hotspot: float = 0.0,
) -> float:
    return pagerank_score * (1.0 + temporal_hotspot)


def compute_overall_risk(
    direct_risks: list[dict[str, Any]],
    transitive_count: int = 0,
) -> float:
    if not direct_risks:
        return 0.0
    avg_direct = sum(r.get("risk_score", 0.0) for r in direct_risks) / len(direct_risks)
    max_direct = max(r.get("risk_score", 0.0) for r in direct_risks)
    breadth_bonus = min(transitive_count / 20.0, 1.0)
    combined = 0.5 * avg_direct + 0.5 * max_direct
    file_term = 8.0 * (1.0 - math.exp(-10.0 * combined))
    return min(file_term + 2.0 * breadth_bonus, 10.0)


def find_test_gaps(
    affected_files: list[str],
    test_paths: set[str],
    covered_paths: set[str] | None = None,
) -> list[str]:
    covered = covered_paths or set()
    gaps: list[str] = []
    for path in affected_files:
        base = os.path.splitext(os.path.basename(path))[0]
        ext = os.path.splitext(path)[1].lstrip(".")
        has_test = any(
            (
                f"test_{base}" in tp
                or f"{base}_test" in tp
                or f"{base}.spec.{ext}" in tp
                or f"{base}.spec." in tp
            )
            for tp in test_paths
        )
        if not has_test and path not in covered:
            gaps.append(path)
    return gaps


def find_reviewers(
    affected_files: list[str],
    owner_map: dict[str, tuple[str | None, str | None, float | None]],
) -> list[dict[str, Any]]:
    scores: dict[str, float] = {}
    emails: dict[str, str] = {}
    for path in affected_files:
        owner_name, owner_email, share = owner_map.get(path, (None, None, None))
        if owner_name and share:
            scores[owner_name] = scores.get(owner_name, 0) + share
            if owner_email and owner_name not in emails:
                emails[owner_name] = owner_email
    sorted_reviewers = sorted(scores.items(), key=lambda x: -x[1])
    return [
        {"name": name, "email": emails.get(name, ""), "relevance_score": round(score, 3)}
        for name, score in sorted_reviewers[:5]
    ]


def analyze_blast_radius(
    changed_files: list[str],
    graph: nx.DiGraph,
    pagerank_scores: dict[str, float] | None = None,
    hotspot_scores: dict[str, float] | None = None,
    owner_map: dict[str, tuple[str | None, str | None, float | None]] | None = None,
    test_paths: set[str] | None = None,
    max_depth: int = 3,
) -> dict[str, Any]:
    changed_set = set(changed_files)
    pr = pagerank_scores or {}
    hs = hotspot_scores or {}

    direct_risks: list[dict[str, Any]] = []
    for path in changed_files:
        risk = score_file(path, pagerank_score=pr.get(path, 0), temporal_hotspot=hs.get(path, 0))
        direct_risks.append({"path": path, "risk_score": round(risk, 4)})

    transitive: set[str] = set()
    for path in changed_files:
        queue = [(path, 0)]
        visited: set[str] = set()
        while queue:
            node, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for pred in graph.predecessors(node):
                if pred not in visited:
                    visited.add(pred)
                    if pred not in changed_set:
                        transitive.add(pred)
                        queue.append((pred, depth + 1))

    transitive_affected = [
        {"path": p, "risk_score": round(score_file(p, pr.get(p, 0), hs.get(p, 0)), 4)}
        for p in sorted(transitive)
    ]

    all_affected = list(changed_set | transitive)
    overall_risk = compute_overall_risk(direct_risks, len(transitive))

    result: dict[str, Any] = {
        "direct_risks": direct_risks,
        "transitive_affected": transitive_affected,
        "overall_risk_score": round(overall_risk, 2),
    }

    if test_paths is not None:
        result["test_gaps"] = find_test_gaps(all_affected, test_paths)

    if owner_map is not None:
        result["recommended_reviewers"] = find_reviewers(all_affected, owner_map)

    return result
