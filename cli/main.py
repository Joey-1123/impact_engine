from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.analyzer import calculate_risk, find_dead_code
from core.git_analyzer import get_changed_functions

import sys
import os
import json


# 🔒 Safe print (respects JSON mode)
def safe_print(json_output, *args, **kwargs):
    if not json_output:
        print(*args, **kwargs)


# -------------------------------
# ANALYZE COMMAND (CLI ONLY)
# -------------------------------
def analyze_command(project_path):
    # import here to avoid side effects in JSON mode
    from core.visualizer import visualize_graph

    deps = extract_project_dependencies(project_path)
    graph = build_graph(deps)

    print("Dependencies:", deps)
    print("Graph Edges:", list(graph.edges()))

    visualize_graph(graph)
    print("Graph saved as graph.png")

    entry_points = [n for n in graph.nodes() if n.endswith("::main")]
    if not entry_points:
        entry_points = [n for n in graph.nodes() if graph.in_degree(n) == 0]

    dead = find_dead_code(graph, entry_points)
    print("\nDead Code (unreachable functions):")
    for d in dead:
        print(f"- {d}")


# -------------------------------
# IMPACT COMMAND (CLI ONLY)
# -------------------------------
def impact_command(project_path, target):
    from core.visualizer import print_impact_tree

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


# -------------------------------
# DIFF COMMAND (USED BY EXTENSION)
# -------------------------------
# -------------------------------
# DIFF COMMAND (USED BY EXTENSION)
# -------------------------------
def diff_command(project_path, json_output=False):
    if not project_path or not os.path.exists(project_path):
        safe_print(json_output, f"Error: path does not exist: {project_path}")
        return

    deps = extract_project_dependencies(project_path)
    if not deps:
        safe_print(json_output, f"No Python files found at {project_path}")
        return

    graph = build_graph(deps)
    changed_funcs = get_changed_functions(deps)

    max_risk = 0
    file_map = {}

    if changed_funcs:
        for func in changed_funcs:
            risk = calculate_risk(graph, func)
            max_risk = max(max_risk, risk)

            parts = func.split("::")
            file_name = parts[0] if len(parts) > 1 else "unknown_file"
            func_name = parts[-1]

            if file_name not in file_map:
                file_map[file_name] = []

            file_map[file_name].append({
                "name": func_name,
                "risk": risk
            })

    results = [
        {"file": f, "functions": funcs}
        for f, funcs in file_map.items()
    ]

    # 🔥 THE FIX: Filter edges to prevent noisy UX and massive JSON payloads
    # Only keep edges if at least one of the nodes is a changed function
    # 🔥 The UX Filter: Remove self-loops (u != v)
    filtered_edges = []
    if changed_funcs:
        changed_set = set(changed_funcs)
        for u, v in graph.edges():
            # If it's not a self loop, AND involves a changed function
            if u != v and (u in changed_set or v in changed_set):
                filtered_edges.append([u, v])

    # 🔥 CRITICAL: ONLY JSON OUTPUT
    if json_output:
        sys.stdout.write(json.dumps({
            "max_risk": max_risk,
            "files": results,
            "edges": filtered_edges
        }, indent=2))  # <--- indent=2 makes it readable in the terminal!
        sys.stdout.flush()
        return

    # CLI output (safe)
    if not results:
        print("No changed functions detected.")
        return

    for file_data in results:
        print(f"\n{file_data['file']}")
        for func in file_data["functions"]:
            print(f"  - {func['name']} (risk={func['risk']})")

    print(f"\nMax Risk: {max_risk}")
def main():
    if len(sys.argv) < 2:
        print("Usage: impact-engine [analyze|impact|diff] [options/targets]")
        return

    command = sys.argv[1]
    
    # Restructured CLI parsing to prevent target functions from being treated as paths
    if command == "impact":
        if len(sys.argv) < 3:
            print("Usage: impact-engine impact <function>")
            return
        target = sys.argv[2]
        project_path = os.getcwd() # Default to current directory for impact
        
    else:
        # For analyze and diff, check if an optional path is provided
        project_path = os.getcwd()
        if len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
            project_path = os.path.abspath(sys.argv[2])

    if not os.path.exists(project_path):
        print(f"Error: path does not exist: {project_path}")
        return

    if command == "analyze":
        analyze_command(project_path)

    elif command == "impact":
        impact_command(project_path, target)

    elif command == "diff":
        json_flag = any(opt in sys.argv for opt in ["--json", "--jsonc"])
        diff_command(project_path, json_output=json_flag)

    else:
        print("Unknown command")


if __name__ == "__main__":
    main()