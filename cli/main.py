from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.visualizer import print_impact_tree, visualize_graph
from core.analyzer import calculate_risk, find_dead_code
from core.git_analyzer import get_changed_functions
#from core.git_analyzer import get_changed_files, map_lines_to_functions
import sys
import os
import json 

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

def diff_command(json_output=False):
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))

    deps = extract_project_dependencies(BASE_DIR)
    graph = build_graph(deps)

    changed_funcs = get_changed_functions(deps)

    if not changed_funcs:
        if json_output:
            print(json.dumps({"max_risk": 0, "functions": []}))
        else:
            print("No changes detected.")
        return

    results = []
    max_risk = 0

    for func in changed_funcs:
        risk = calculate_risk(graph, func)

        results.append({
            "function": func,
            "risk": risk
        })

        max_risk = max(max_risk, risk)

    if json_output:
        print(json.dumps({
            "max_risk": max_risk,
            "functions": results
        }))
        return

    print("Changed functions:")
    for r in results:
        print(f"- {r['function']} (risk={r['risk']})")

    print(f"\nMax Risk: {max_risk}")
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
        json_flag = "--json" in sys.argv
        diff_command(json_output=json_flag)

    else:
        print("Unknown command")