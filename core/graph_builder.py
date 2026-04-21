import networkx as nx

def build_graph(dependencies):
    graph = nx.DiGraph()
    for caller, callees in dependencies.items():
        graph.add_node(caller)
        for callee in callees:
            graph.add_node(callee)
            graph.add_edge(caller, callee)
            print(f"DEBUG EDGE ADDED: {caller} -> {callee}")  # debug

    return graph