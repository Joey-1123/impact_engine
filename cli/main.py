from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.visualizer import print_impact_tree, visualize_graph
from core.analyzer import calculate_risk, find_dead_code
from core.git_analyzer import get_changed_functions
import sys
import os
import json 

def analyze_command(project_path):
    deps = extract_project_dependencies(project_path)
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


def impact_command(project_path, target):
    deps = extract_project_dependencies(project_path)
    graph = build_graph(deps)

    matches = [n for n in graph.nodes() if n.endswith(f"::{target}")]

    if not matches:
        print(f"Function '{target}' not found.")
        return

    for match in matches:
        print(f"\nImpact Tree for '{match}':")
        print_impact_tree(graph, match)

        risk = calculate_risk(graph, match)
        print(f"Risk Score for '{match}': {risk}")

def diff_command(project_path, json_output=False):
    if not project_path or not os.path.exists(project_path):
        print(f"Error: path does not exist: {project_path}")
        return

    deps = extract_project_dependencies(project_path)
    if not deps:
        print(f"Error: no Python files found at {project_path}")
        return

    graph = build_graph(deps)

    changed_funcs = get_changed_functions(deps)

    results = []
    max_risk = 0

    def normalize_changed_function(func):
        if isinstance(func, dict):
            raw_full_name = func.get("fullName") or func.get("function") or ""
            function_name = func.get("function") or raw_full_name.split("::")[-1]
            file_name = func.get("file")
        elif isinstance(func, (list, tuple)) and func:
            if len(func) >= 2:
                file_name = func[0]
                function_name = func[1]
                raw_full_name = f"{file_name}::{function_name}"
            else:
                raw_full_name = str(func[0])
                file_name = raw_full_name.split("::")[0] if "::" in raw_full_name else None
                function_name = raw_full_name.split("::")[-1]
        else:
            raw_full_name = str(func)
            function_name = raw_full_name.split("::")[-1]
            file_name = raw_full_name.split("::")[0] if "::" in raw_full_name else None

        if file_name and not raw_full_name.startswith(f"{file_name}::"):
            raw_full_name = f"{file_name}::{function_name}"

        return {
            "file": file_name,
            "function": function_name,
            "fullName": raw_full_name,
        }

    if changed_funcs:
        for func in changed_funcs:
            normalized = normalize_changed_function(func)
            risk = calculate_risk(graph, func)

            results.append({
                "file": normalized["file"],
                "function": normalized["function"],
                "fullName": normalized["fullName"],
                "risk": risk
            })

            max_risk = max(max_risk, risk)

    
    if json_output:
        print(json.dumps({
            "max_risk": max_risk,
            "functions": results
        }))
        return

    # CLI mode (optional)
    if not results:
        print("No changes detected.")
        return

    print("Changed functions:")
    for r in results:
        print(f"- {r['function']} (risk={r['risk']})")

    print(f"\nMax Risk: {max_risk}")

def resolve_path():
    if len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
        path = os.path.abspath(sys.argv[2])
        return path

    cwd = os.getcwd()
    return cwd


def main():
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: impact-engine [analyze|impact|diff]")
        return

    command = sys.argv[1]
    project_path = resolve_path()

    if project_path and not os.path.exists(project_path):
        print(f"Error: path does not exist: {project_path}")
        return

    if command == "analyze":
        analyze_command(project_path)

    elif command == "impact":
        if len(sys.argv) < 3:
            print("Usage: impact-engine impact <function>")
            return
        target = sys.argv[2]
        impact_command(project_path, target)

    elif command == "diff":
        json_flag = any(opt in sys.argv for opt in ["--json", "--jsonc"])
        diff_command(project_path, json_output=json_flag)

    else:
        print("Unknown command")


if __name__ == "__main__":
    main()
