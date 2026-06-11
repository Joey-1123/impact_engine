from typing import Optional, Set, List, Dict
import networkx as nx

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


def print_impact_tree(graph: nx.DiGraph, target: str) -> None:
    reversed_graph = graph.reverse()
    visited: Set[str] = set([target])

    def dfs(node: str, level: int = 0) -> None:
        indent = "    " * level

        for neighbor in reversed_graph.neighbors(node):
            if neighbor not in visited:
                print(f"{indent}├── {neighbor}")
                visited.add(neighbor)
                dfs(neighbor, level + 1)

    print(target)
    dfs(target)


def render_terminal_graph(
    graph: nx.DiGraph,
    changed_nodes: Optional[Set[str]] = None,
    max_nodes: int = 200,
    max_depth: int = 4,
    max_children: int = 12,
    changed_only: bool = False,
) -> None:
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
    changed_nodes_set = set(changed_nodes or [])
    focus_nodes = [n for n in changed_nodes_set if n in graph] if changed_nodes_set else []

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

    visited: Set[str] = set()

    def add_branch(parent, node: str, depth: int) -> None:
        if depth > max_depth:
            parent.add("[dim]…")
            return

        if node in visited:
            parent.add(f"[dim]{node} (seen)")
            return

        visited.add(node)

        label = node.split("::")[-1]
        risk = graph.out_degree(node)
        if node in changed_nodes_set:
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


def print_complexity_table(
    function_complexity: Dict[str, int],
    limit: int = 20,
) -> None:
    sorted_funcs = sorted(function_complexity.items(), key=lambda x: -x[1])[:limit]
    if not sorted_funcs:
        print("No complexity data available.")
        return

    print("\nCyclomatic Complexity (top {}):".format(limit))
    print(f"{'Function':<50} {'Complexity':>10} {'Risk Level':>12}")
    print("-" * 74)
    for func, comp in sorted_funcs:
        if comp >= 10:
            level = "HIGH"
        elif comp >= 5:
            level = "MEDIUM"
        else:
            level = "LOW"
        func_short = func.split("::")[-1] if "::" in func else func
        print(f"{func_short:<50} {comp:>10} {level:>12}")


def print_complexity_json(function_complexity: Dict[str, int], limit: int = 20) -> str:
    import json
    sorted_funcs = sorted(function_complexity.items(), key=lambda x: -x[1])[:limit]
    payload = [
        {"function": k, "complexity": v}
        for k, v in sorted_funcs
    ]
    return json.dumps(payload, indent=2)


def visualize_graph(graph: nx.DiGraph, output_file: str = "graph", max_nodes: int = 500) -> None:
    if Digraph is None:
        print("Graphviz not installed, skipping visualization")
        return

    dot = Digraph()

    nodes = list(graph.nodes())[:max_nodes]
    node_set = set(nodes)

    for node in nodes:
        dot.node(node)

    for edge in graph.edges():
        if edge[0] in node_set and edge[1] in node_set:
            dot.edge(edge[0], edge[1])

    try:
        dot.render(output_file, format="png", cleanup=True)
    except Exception as exc:
        print("Warning: cannot render graph. Ensure Graphviz is installed and available on PATH.")
        print(f"Graphviz error: {exc}")
