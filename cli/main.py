from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.visualizer import print_impact_tree, visualize_graph
from core.analyzer import calculate_risk, find_dead_code
from core.git_analyzer import get_changed_files, map_files_to_functions
import os
import sys

def analyze_command(file_path):
    deps = extract_project_dependencies(file_path)
    graph = build_graph(deps)

    print("Dependencies:", deps)
    print("Graph Edges:", list(graph.edges()))

    visualize_graph(graph)
    print("Graph saved as graph.png")

    # Entry points
    entry_points = [n for n in graph.nodes() if n.endswith("::main")]
    if not entry_points:
        entry_points = [n for n in graph.nodes() if graph.in_degree(n) == 0]

    # Dead code
    dead = find_dead_code(graph, entry_points)
    print("\nDead Code (unreachable functions):")
    for d in dead:
        print(f"- {d}")


def impact_command(file_path, target):
    deps = extract_project_dependencies(file_path)
    graph = build_graph(deps)

    matches = [n for n in graph.nodes if n.endswith(f"::{target}")]

    if not matches:
        print(f"Function '{target}' not found.")
        return

    for match in matches:
        print(f"\nImpact Tree for '{match}':")
        print_impact_tree(graph, match)

        risk = calculate_risk(graph, match)
        print(f"Risk Score for '{match}': {risk}")
def diff_command():
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))

    deps = extract_project_dependencies(BASE_DIR)
    graph = build_graph(deps)

    changed_files = get_changed_files()

    if not changed_files:
        print("No changed Python files detected.")
        return

    print("Changed files:")
    for f in changed_files:
        print(f"- {f}")

    changed_funcs = map_files_to_functions(changed_files, deps)

    if not changed_funcs:
        print("\nNo functions detected in changed files.")
        return

    print("\nChanged functions:")
    for func in changed_funcs:
        print(f"- {func}")

    for func in changed_funcs:
        print(f"\nImpact for '{func}':")
        print_impact_tree(graph, func)

        risk = calculate_risk(graph, func)
        print(f"Risk Score: {risk}")

def main():
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(BASE_DIR, "tests")

    if len(sys.argv) < 2:
        print("Usage: impact-engine [analyze|impact|diff]")
        return

    command = sys.argv[1]

    if command == "analyze":
        analyze_command(file_path)

    elif command == "impact":
        if len(sys.argv) < 3:
            print("Usage: impact-engine impact <function>")
            return
        target = sys.argv[2]
        impact_command(file_path, target)

    elif command == "diff":
        diff_command()

    else:
        print("Unknown command")