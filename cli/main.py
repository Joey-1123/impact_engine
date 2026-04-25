from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.visualizer import print_impact_tree, visualize_graph
from core.analyzer import calculate_risk, find_dead_code
from core.git_analyzer import get_changed_lines, map_lines_to_functions
import sys
import os

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

    file_changes = get_changed_lines()

    if not file_changes:
        print("No changes detected.")
        return

    changed_funcs = []

    for file, lines in file_changes.items():
        abs_path = os.path.join(BASE_DIR, file)

        if not os.path.exists(abs_path):
            continue

        funcs = map_lines_to_functions(abs_path, lines)

        for func in funcs:
            namespaced = f"{os.path.basename(file)}::{func}"
            changed_funcs.append(namespaced)

    if not changed_funcs:
        print("No function-level changes detected.")
        return

    print("Changed functions:")
    for f in changed_funcs:
        print(f"- {f}")

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