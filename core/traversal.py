# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from typing import Set
import networkx as nx


def get_impact(graph: nx.DiGraph, target: str) -> Set[str]:
    if not graph.has_node(target):
        return set()

    reversed_graph = graph.reverse()

    visited: Set[str] = set()
    stack = [target]

    while stack:
        node = stack.pop()

        for neighbor in reversed_graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)

    return visited
