def get_impact(graph, target):
    
    # Reverse graph: callee → caller
    if target not in graph:
        return set()
    
    
    reversed_graph = graph.reverse()

    visited = set()
    stack = [target]

    while stack:
        node = stack.pop()

        for neighbor in reversed_graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)

    return visited