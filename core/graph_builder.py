# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from typing import Dict, List
import networkx as nx


def build_graph(dependencies: Dict[str, List[str]]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for caller, callees in dependencies.items():
        graph.add_node(caller)
        for callee in callees:
            graph.add_node(callee)
            graph.add_edge(caller, callee)

    return graph
