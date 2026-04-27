try:
    from graphviz import Digraph
except ImportError:
    Digraph = None


def print_impact_tree(graph, target):
    reversed_graph = graph.reverse()
    visited = set([target])   # avoid self loop

    def dfs(node, level=0):
        indent = "    " * level

        for neighbor in reversed_graph.neighbors(node):
            if neighbor not in visited:
                print(f"{indent}├── {neighbor}")
                visited.add(neighbor)
                dfs(neighbor, level + 1)

    print(target)
    dfs(target)


def visualize_graph(graph, output_file="graph"):
    #  SAFE GUARD HERE (correct place)
    if Digraph is None:
        print("Graphviz not installed, skipping visualization")
        return

    dot = Digraph()

    for node in graph.nodes():
        dot.node(node)

    for edge in graph.edges():
        dot.edge(edge[0], edge[1])

    try:
        dot.render(output_file, format="png", cleanup=True)
    except Exception as exc:
        print("Warning: cannot render graph. Ensure Graphviz is installed and available on PATH.")
        print(f"Graphviz error: {exc}")