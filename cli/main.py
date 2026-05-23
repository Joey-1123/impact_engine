from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.analyzer import calculate_risk, find_dead_code
from core.git_analyzer import get_changed_functions
from core.summary import build_analysis_summary, build_analysis_summary_payload
from core.version import __version__

import sys
import os
import json


# 🔒 Safe print (respects JSON mode)
def safe_print(json_output, *args, **kwargs):
    if not json_output:
        print(*args, **kwargs)


def _get_flag_value(argv, *flags, default=None):
    for flag in flags:
        if flag in argv:
            index = argv.index(flag)
            if index + 1 < len(argv):
                value = argv[index + 1]
                if not value.startswith("--"):
                    return value
    return default


def _has_flag(argv, *flags):
    return any(flag in argv for flag in flags)


def _parse_int_flag(argv, *flags, default):
    value = _get_flag_value(argv, *flags, default=str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _resolve_project_path(argv):
    project_path = _get_flag_value(argv, "--project", "-p")
    if project_path:
        return os.path.abspath(project_path)

    skip_next = False
    value_flags = {"--project", "-p", "--depth", "--children", "--limit"}

    for token in argv[2:]:
        if skip_next:
            skip_next = False
            continue

        if token in value_flags:
            skip_next = True
            continue

        if token.startswith("--"):
            continue

        return os.path.abspath(token)

    return os.getcwd()


# -------------------------------
# ANALYZE COMMAND (CLI ONLY)
# -------------------------------
def analyze_command(project_path, *, max_depth=3, max_children=12, changed_only=False):
    from core.visualizer import render_terminal_graph

    deps = extract_project_dependencies(project_path)
    graph = build_graph(deps)
    changed_funcs = get_changed_functions(deps)

    entry_points = [n for n in graph.nodes() if n.endswith("::main")]
    if not entry_points:
        entry_points = [n for n in graph.nodes() if graph.in_degree(n) == 0]

    print("Impact Summary")
    print(f"- Functions: {graph.number_of_nodes()}")
    print(f"- Edges: {graph.number_of_edges()}")
    print(f"- Changed functions: {len(changed_funcs)}")

    if changed_funcs:
        print("\nChanged functions:")
        for func in changed_funcs[:20]:
            print(f"- {func}")
        if len(changed_funcs) > 20:
            print(f"- ... {len(changed_funcs) - 20} more")

    print("\nTerminal Graph:")
    render_terminal_graph(
        graph,
        changed_nodes=changed_funcs,
        max_depth=max_depth,
        max_children=max_children,
        changed_only=changed_only,
    )

    dead = find_dead_code(graph, entry_points)
    print("\nDead Code (unreachable functions):")
    for d in dead:
        print(f"- {d}")


def graph_command(project_path, *, max_depth=4, max_children=12, changed_only=False):
    from core.visualizer import render_terminal_graph

    deps = extract_project_dependencies(project_path)
    graph = build_graph(deps)
    changed_funcs = get_changed_functions(deps)

    print("Terminal Graph:\n")
    render_terminal_graph(
        graph,
        changed_nodes=changed_funcs,
        max_depth=max_depth,
        max_children=max_children,
        changed_only=changed_only,
    )


def summary_command(project_path, *, json_output=False, limit=10):
    deps = extract_project_dependencies(project_path)
    graph = build_graph(deps)
    changed_funcs = get_changed_functions(deps)
    entry_points = [n for n in graph.nodes() if n.endswith("::main")]
    if not entry_points:
        entry_points = [n for n in graph.nodes() if graph.in_degree(n) == 0]

    dead_nodes = find_dead_code(graph, entry_points)
    summary = build_analysis_summary(
        graph,
        changed_nodes=changed_funcs,
        dead_nodes=dead_nodes,
        limit=limit,
    )

    if json_output:
        payload = build_analysis_summary_payload(
            graph,
            changed_nodes=changed_funcs,
            dead_nodes=dead_nodes,
            limit=limit,
        )
        sys.stdout.write(json.dumps(payload, indent=2))
        sys.stdout.flush()
        return

    print("Impact Summary")
    print(f"- Nodes: {summary['counts']['nodes']}")
    print(f"- Edges: {summary['counts']['edges']}")
    print(f"- Changed: {summary['counts']['changed']}")
    print(f"- Dead: {summary['counts']['dead']}")

    print("\nTop blast-radius hotspots:")
    for item in summary["top_hotspots"]:
        marker = "*" if item["changed"] else "-"
        print(
            f"{marker} {item['node']} "
            f"(risk={item['risk']}, outgoing={item['outgoing']}, incoming={item['incoming']})"
        )

    if summary["changed_hotspots"]:
        print("\nChanged blast-radius hotspots:")
        for item in summary["changed_hotspots"]:
            print(f"- {item['node']} (risk={item['risk']})")

    if summary["dead_nodes"]:
        print("\nDead code sample:")
        for node in summary["dead_nodes"]:
            print(f"- {node}")


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
        print("Usage: impact-engine [analyze|graph|summary|impact|diff|version] [options/targets]")
        return

    if _has_flag(sys.argv, "--version", "-V") or sys.argv[1] == "version":
        print(f"impact-engine {__version__}")
        return

    command = sys.argv[1]

    # Restructured CLI parsing to prevent target functions from being treated as paths
    if command == "impact":
        if len(sys.argv) < 3:
            print("Usage: impact-engine impact <function>")
            return
        target = sys.argv[2]
        if target.startswith("--"):
            print("Usage: impact-engine impact <function>")
            return
        project_path = _get_flag_value(sys.argv, "--project", "-p") or os.getcwd()
    else:
        project_path = _resolve_project_path(sys.argv)

    if not os.path.exists(project_path):
        print(f"Error: path does not exist: {project_path}")
        return

    max_depth = int(_get_flag_value(sys.argv, "--depth", default="3") or "3")
    max_children = int(_get_flag_value(sys.argv, "--children", default="12") or "12")
    changed_only = _has_flag(sys.argv, "--changed-only", "--focused")
    summary_json = _has_flag(sys.argv, "--json", "--jsonc")
    summary_limit = _parse_int_flag(sys.argv, "--limit", default=10)

    if command == "analyze":
        analyze_command(
            project_path,
            max_depth=max_depth,
            max_children=max_children,
            changed_only=changed_only,
        )

    elif command == "graph":
        graph_command(
            project_path,
            max_depth=max_depth,
            max_children=max_children,
            changed_only=changed_only,
        )

    elif command == "summary":
        summary_command(
            project_path,
            json_output=summary_json,
            limit=summary_limit,
        )

    elif command == "impact":
        impact_command(project_path, target)

    elif command == "diff":
        json_flag = any(opt in sys.argv for opt in ["--json", "--jsonc"])
        diff_command(project_path, json_output=json_flag)

    else:
        print("Unknown command")


if __name__ == "__main__":
    main()
