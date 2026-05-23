try:
    from graphviz import Digraph
except ImportError:
    Digraph = None

try:
    from rich.console import Console
    from rich.tree import Tree
except ImportError:
    Console = None
    Tree = None


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


def render_terminal_graph(
    graph,
    changed_nodes=None,
    max_nodes=200,
    max_depth=4,
    max_children=12,
    changed_only=False,
):
    """
    Render a compact dependency graph in the terminal.

    This favors readability over completeness by showing the most connected
    roots first and limiting depth for very large repositories.
    """
    if Console is None or Tree is None:
        print("Rich is not installed, falling back to plain text output.")
        print("Nodes:")
        for node in sorted(graph.nodes()):
            print(f"- {node}")
        print("\nEdges:")
        for source, target in graph.edges():
            print(f"- {source} -> {target}")
        return

    console = Console()
    changed_nodes = set(changed_nodes or [])
    focus_nodes = [n for n in changed_nodes if n in graph] if changed_nodes else []

    if changed_only and focus_nodes:
        roots = sorted(
            focus_nodes,
            key=lambda node: (-graph.out_degree(node), node)
        )[:max_nodes]
        title = "Impact Graph (focused on changed functions)"
    else:
        roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
        if not roots:
            roots = list(graph.nodes())
        roots = sorted(
            roots,
            key=lambda node: (-graph.out_degree(node), node)
        )[:max_nodes]
        title = "Impact Graph"

    tree = Tree(title)

    visited = set()

    def add_branch(parent, node, depth):
        if depth > max_depth:
            parent.add("[dim]…")
            return

        if node in visited:
            parent.add(f"[dim]{node} (seen)")
            return

        visited.add(node)

        label = node.split("::")[-1]
        risk = graph.out_degree(node)
        if node in changed_nodes:
            prefix = "[magenta]"
            suffix = "[/]"
        elif risk >= 5:
            prefix = "[red]"
            suffix = "[/]"
        elif risk >= 2:
            prefix = "[yellow]"
            suffix = "[/]"
        else:
            prefix = "[green]"
            suffix = "[/]"
        branch = parent.add(f"{prefix}{label}{suffix} [dim]({risk} outgoing)[/]")

        children = sorted(graph.successors(node), key=lambda n: (-graph.out_degree(n), n))
        for child in children[:max_children]:
            add_branch(branch, child, depth + 1)

        if len(children) > max_children:
            branch.add(f"[dim]… {len(children) - max_children} more")

    for root in roots:
        add_branch(tree, root, 0)

    console.print(tree)


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
