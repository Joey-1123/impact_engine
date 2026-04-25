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


def find_dead_code(graph, entry_points):
    """
    Dead code = nodes NOT reachable from entry points
    """
    visited = set()
    stack = list(entry_points)

    while stack:
        node = stack.pop()

        if node not in visited:
            visited.add(node)

            for neighbor in graph.neighbors(node):
                stack.append(neighbor)

    dead_nodes = [node for node in graph.nodes() if node not in visited]

    return dead_nodes