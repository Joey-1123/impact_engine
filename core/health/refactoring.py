from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import networkx as nx


@dataclass
class RefactoringSuggestion:
    plan: str
    evidence: str
    confidence: float = 0.5
    effort_bucket: str = "medium"
    blast_radius: int = 0
    file_path: str = ""
    detector_name: str = ""


def _greedy_mfas(members: list[str], edges: list[tuple[str, str]]) -> list[tuple[str, str]]:
    nodes = list(members)
    adj_out: dict[str, set[str]] = {n: set() for n in nodes}
    adj_in: dict[str, set[str]] = {n: set() for n in nodes}
    node_set = set(nodes)
    for u, v in edges:
        if u in node_set and v in node_set and u != v:
            adj_out[u].add(v)
            adj_in[v].add(u)

    remaining = set(nodes)
    s1: list[str] = []
    s2: list[str] = []

    def _out_deg(n: str) -> int:
        return len(adj_out[n] & remaining)

    def _in_deg(n: str) -> int:
        return len(adj_in[n] & remaining)

    while remaining:
        progressed = True
        while progressed:
            progressed = False
            for n in sorted(remaining):
                if _out_deg(n) == 0:
                    s2.insert(0, n)
                    remaining.discard(n)
                    progressed = True
            for n in sorted(remaining):
                if n in remaining and _in_deg(n) == 0:
                    s1.append(n)
                    remaining.discard(n)
                    progressed = True
        if remaining:
            best = max(sorted(remaining), key=lambda n: _out_deg(n) - _in_deg(n))
            s1.append(best)
            remaining.discard(best)

    ordering = s1 + s2
    pos = {n: i for i, n in enumerate(ordering)}
    cut = [(u, v) for (u, v) in edges if u in pos and v in pos and pos[u] > pos[v]]
    return sorted(set(cut))


def detect_cycles(graph: nx.DiGraph, max_cycle_files: int = 20, max_cut_edges: int = 4) -> list[RefactoringSuggestion]:
    suggestions: list[RefactoringSuggestion] = []
    seen: set[frozenset[str]] = set()

    sccs = list(nx.strongly_connected_components(graph))
    for scc in sccs:
        if len(scc) < 2:
            continue
        if len(scc) > max_cycle_files:
            continue

        members = sorted(scc)
        key = frozenset(members)
        if key in seen:
            continue
        seen.add(key)

        edges = [(u, v) for (u, v) in graph.edges() if u in scc and v in scc]
        cut = _greedy_mfas(members, edges)

        if not cut or len(cut) > max_cut_edges:
            continue

        anchor = members[0]
        edge_desc = "; ".join(f"{u} → {v}" for u, v in cut[:max_cut_edges])
        suggestions.append(
            RefactoringSuggestion(
                plan=f"Break {len(members)}-file import cycle by removing or inverting these edges: {edge_desc}",
                evidence=f"Circular dependency among {len(members)} files: {', '.join(members[:5])}"
                + (f" and {len(members) - 5} more" if len(members) > 5 else ""),
                confidence=0.7,
                effort_bucket="medium",
                blast_radius=sum(graph.in_degree(n) for n in members),
                file_path=anchor,
                detector_name="break_cycle",
            )
        )

    return suggestions


def detect_split_files(
    graph: nx.DiGraph,
    complexities: dict[str, int] | None = None,
) -> list[RefactoringSuggestion]:
    suggestions: list[RefactoringSuggestion] = []
    complexities = complexities or {}
    file_groups: dict[str, set[str]] = {}
    for node in graph.nodes():
        fpath = node.split("::")[0] if "::" in node else node
        file_groups.setdefault(fpath, set()).add(node)

    for fpath, funcs in file_groups.items():
        if len(funcs) < 5:
            continue
        total_ccn = sum(complexities.get(f, 1) for f in funcs)
        if total_ccn < 30:
            continue
        suggestions.append(
            RefactoringSuggestion(
                plan=f"Split {fpath} into smaller modules "
                f"(currently {len(funcs)} functions, cyclomatic complexity sum {total_ccn})",
                evidence=f"File contains {len(funcs)} functions with total CCN={total_ccn}, "
                f"suggesting multiple responsibilities",
                confidence=0.5,
                effort_bucket="medium",
                blast_radius=graph.in_degree(fpath),
                file_path=fpath,
                detector_name="split_file",
            )
        )

    return suggestions


def rank_suggestions(
    suggestions: list[RefactoringSuggestion],
    graph: nx.DiGraph | None = None,
) -> list[RefactoringSuggestion]:
    scored: list[tuple[float, RefactoringSuggestion]] = []
    for s in suggestions:
        centrality = 1.0
        if graph and s.file_path in graph:
            centrality = 1.0 + math.log1p(graph.in_degree(s.file_path))
        blast = 1.0 + math.log1p(s.blast_radius)
        confidence = s.confidence
        score = blast * centrality * confidence
        scored.append((score, s))

    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored]
