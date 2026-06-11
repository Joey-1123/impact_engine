from typing import List, Set, Dict, Any, Optional
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
        if n.endswith("::main"):
            entry_points.append(n)

    if not entry_points:
        entry_points = [n for n in graph.nodes() if graph.in_degree(n) == 0]

    if main_block_functions:
        for func in main_block_functions:
            if func not in entry_points and func in graph:
                entry_points.append(func)

    return entry_points


def build_impact_report(
    graph: nx.DiGraph,
    entry_points: Optional[List[str]] = None,
    main_block_functions: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    if entry_points is None:
        entry_points = find_entry_points(graph, main_block_functions=main_block_functions)

    cycles = find_cycles(graph)

    return {
        "cycles": cycles,
        "cycle_count": len(cycles),
        "entry_points": entry_points,
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
    }
