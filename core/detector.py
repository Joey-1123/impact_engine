# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from typing import List, Set, Optional
import networkx as nx


def find_cycles(graph: nx.DiGraph) -> List[List[str]]:
    cycles: List[List[str]] = []
    try:
        for cycle in nx.simple_cycles(graph):
            cycles.append(cycle)
    except nx.NetworkXNoCycle:
        pass
    return cycles


def find_entry_points(
    graph: nx.DiGraph,
    main_block_functions: Optional[Set[str]] = None,
) -> List[str]:
    entry_points: List[str] = []

    for n in graph.nodes():
        name = n.split("::")[-1]
        func_name = name.split(".")[-1] if "." in name else name
        if func_name in {"main", "run", "entrypoint", "start"}:
            entry_points.append(n)

    if not entry_points:
        entry_points = [n for n in graph.nodes() if graph.in_degree(n) == 0]

    if main_block_functions:
        for func in main_block_functions:
            if func not in entry_points and func in graph:
                entry_points.append(func)

    return entry_points

