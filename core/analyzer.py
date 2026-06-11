from typing import List, Set
import networkx as nx
from core.traversal import get_impact


def calculate_risk(graph: nx.DiGraph, target: str) -> int:
    return len(get_impact(graph, target))


def find_dead_code(graph: nx.DiGraph, entry_points: List[str]) -> List[str]:
    visited: Set[str] = set()
    stack = list(entry_points)

    while stack:
        node = stack.pop()

        if node not in visited:
            visited.add(node)

            for neighbor in graph.neighbors(node):
                stack.append(neighbor)

    dead_nodes = [node for node in graph.nodes() if node not in visited]

    return dead_nodes
