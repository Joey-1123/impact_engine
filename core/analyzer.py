def calculate_risk(graph, target):
    """
    Risk = number of downstream impacted nodes
    """
    reversed_graph = graph.reverse()

    visited = set()
    stack = [target]

    while stack:
        node = stack.pop()

        for neighbor in reversed_graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)

    return len(visited)


def find_dead_code(graph):
    """
    Dead code = nodes with no incoming edges
    """
    dead_nodes = []

    for node in graph.nodes():
        if graph.in_degree(node) == 0:
            dead_nodes.append(node)

    return dead_nodes