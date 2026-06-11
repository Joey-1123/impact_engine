# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import sys
import os
import json

from core.extractor import extract_project_dependencies, extract_project_dependencies_rich
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.analyzer import calculate_risk, find_dead_code
from core.git_analyzer import get_changed_functions
from core.summary import build_analysis_summary, build_analysis_summary_payload
from core.version import __version__
from core.config import load_config, merge_config
from core.comparator import compare_branches
from core.exporter import export_mermaid, export_mermaid_with_changes, export_sarif
from core.detector import find_cycles, find_entry_points


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


def _load_and_merge_config(project_path, argv):
    config = load_config(project_path)
    cli_args = {
        "max_depth": _parse_int_flag(argv, "--depth", default=config.get("max_depth", 3)),
        "max_children": _parse_int_flag(argv, "--children", default=config.get("max_children", 12)),
        "limit": _parse_int_flag(argv, "--limit", default=config.get("limit", 10)),
        "json_output": _has_flag(argv, "--json", "--jsonc") or config.get("json_output", False),
        "changed_only": _has_flag(argv, "--changed-only", "--focused"),
    }
    return merge_config(cli_args, config)


def _run_analysis(project_path, use_cache=True):
    if use_cache:
        try:
            from core.cache import extract_project_dependencies_cached
            deps, linenos, complexities = extract_project_dependencies_cached(project_path, use_cache=True)
        except Exception:
            deps, linenos, complexities = extract_project_dependencies_rich(project_path)
    else:
        deps, linenos, complexities = extract_project_dependencies_rich(project_path)
    graph = build_graph(deps)
    changed_funcs = get_changed_functions(deps)
    entry_points = find_entry_points(graph)
    dead_nodes = find_dead_code(graph, entry_points)
    cycles = find_cycles(graph)
    return deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities


def analyze_command(project_path, *, max_depth=3, max_children=12, changed_only=False):
    from core.visualizer import render_terminal_graph, print_complexity_table

    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path)

    print("Impact Summary")
    print(f"- Functions: {graph.number_of_nodes()}")
    print(f"- Edges: {graph.number_of_edges()}")
    print(f"- Changed functions: {len(changed_funcs)}")
    print(f"- Dead functions: {len(dead_nodes)}")
    if cycles:
        print(f"- Circular dependencies: {len(cycles)}")

    if changed_funcs:
        print("\nChanged functions:")
        for func in changed_funcs[:20]:
            loc = linenos.get(func, "")
            loc_str = f" [line {loc}]" if loc else ""
            print(f"- {func}{loc_str}")
        if len(changed_funcs) > 20:
            print(f"- ... {len(changed_funcs) - 20} more")

    if cycles:
        print("\nCircular dependencies detected:")
        for cycle in cycles[:5]:
            print(f"  {' -> '.join(c.split('::')[-1] for c in cycle)}")
        if len(cycles) > 5:
            print(f"  ... {len(cycles) - 5} more")

    print("\nTerminal Graph:")
    render_terminal_graph(
        graph,
        changed_nodes=changed_funcs,
        max_depth=max_depth,
        max_children=max_children,
        changed_only=changed_only,
    )

    print_complexity_table(complexities)

    print("\nDead Code (unreachable functions):")
    for d in dead_nodes[:10]:
        print(f"- {d}")
    if len(dead_nodes) > 10:
        print(f"- ... {len(dead_nodes) - 10} more")


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
    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path)

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
        payload["cycles"] = cycles
        sys.stdout.write(json.dumps(payload, indent=2))
        sys.stdout.flush()
        return

    print("Impact Summary")
    print(f"- Nodes: {summary['counts']['nodes']}")
    print(f"- Edges: {summary['counts']['edges']}")
    print(f"- Changed: {summary['counts']['changed']}")
    print(f"- Dead: {summary['counts']['dead']}")
    if cycles:
        print(f"- Cycles: {len(cycles)}")

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


def impact_command(project_path, target):
    from core.visualizer import print_impact_tree

    deps, graph, *_ = _run_analysis(project_path)

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

    filtered_edges = []
    if changed_funcs:
        changed_set = set(changed_funcs)
        for u, v in graph.edges():
            if u != v and (u in changed_set or v in changed_set):
                filtered_edges.append([u, v])

    if json_output:
        sys.stdout.write(json.dumps({
            "max_risk": max_risk,
            "files": results,
            "edges": filtered_edges
        }, indent=2))
        sys.stdout.flush()
        return

    if not results:
        print("No changed functions detected.")
        return

    for file_data in results:
        print(f"\n{file_data['file']}")
        for func in file_data["functions"]:
            print(f"  - {func['name']} (risk={func['risk']})")

    print(f"\nMax Risk: {max_risk}")


def complexity_command(project_path, json_output=False, limit=20):
    from core.visualizer import print_complexity_table, print_complexity_json

    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path)

    if json_output:
        print(print_complexity_json(complexities, limit=limit))
        return

    print_complexity_table(complexities, limit=limit)


def mermaid_command(project_path, output_file=None, show_changed=False):
    deps, graph, changed_funcs, *_ = _run_analysis(project_path)

    if show_changed and changed_funcs:
        output = export_mermaid_with_changes(graph, changed_nodes=set(changed_funcs))
    else:
        output = export_mermaid(graph)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Exported to {output_file}")
    else:
        print(output)


def sarif_command(project_path, output_file=None):
    deps, graph, changed_funcs, entry_points, dead_nodes, *_ = _run_analysis(project_path)

    sarif = export_sarif(
        graph,
        changed_nodes=changed_funcs,
        dead_nodes=dead_nodes,
        tool_version=__version__,
    )

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(sarif)
        print(f"Exported to {output_file}")
    else:
        print(sarif)


def compare_command(project_path, base_ref="main", json_output=False):
    result = compare_branches(project_path, base_ref=base_ref)

    if json_output:
        print(json.dumps(result, indent=2))
        return

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    s = result["summary"]
    print(f"Comparing {result['base_ref']} vs {result['head_ref']}")
    print(f"Merge base: {result['merge_base']}")
    print(f"\nSummary:")
    print(f"  New changes:     {s['new_changes']}")
    print(f"  Resolved:        {s['resolved']}")
    print(f"  Still changed:   {s['still_changed']}")
    print(f"  Total on base:   {s['total_on_base']}")
    print(f"  Total on head:   {s['total_on_head']}")
    print(f"  Risk delta:      {result['risk_delta']:+d}")

    if result["new_changes"]:
        print(f"\nNew functions:")
        for func in result["new_changes"][:10]:
            print(f"  + {func}")
        if len(result["new_changes"]) > 10:
            print(f"  ... {len(result['new_changes']) - 10} more")

    if result["resolved_changes"]:
        print(f"\nResolved functions:")
        for func in result["resolved_changes"][:10]:
            print(f"  - {func}")
        if len(result["resolved_changes"]) > 10:
            print(f"  ... {len(result['resolved_changes']) - 10} more")


def cycles_command(project_path, json_output=False):
    deps, graph, *_ = _run_analysis(project_path)
    cycles = find_cycles(graph)

    if json_output:
        print(json.dumps({"cycles": cycles, "count": len(cycles)}, indent=2))
        return

    if not cycles:
        print("No circular dependencies found.")
        return

    print(f"Found {len(cycles)} circular dependencie(s):\n")
    for i, cycle in enumerate(cycles, 1):
        print(f"  Cycle {i}: {' -> '.join(c.split('::')[-1] for c in cycle)}")


def watch_command(project_path, max_depth=3, max_children=12):
    from core.watcher import watch

    def on_change(changed_files):
        print(f"\n[{len(changed_files)} file(s) changed] Re-running analysis...\n")
        analyze_command(project_path, max_depth=max_depth, max_children=max_children, changed_only=True)

    print(f"Watching {project_path} for changes... (Ctrl+C to stop)")
    watch(project_path, on_change)


def main():
    if len(sys.argv) < 2:
        print("Usage: impact-engine [command] [options]")
        print("Commands: analyze, graph, summary, impact, diff, complexity,")
        print("          mermaid, sarif, compare, cycles, version, watch")
        return

    if _has_flag(sys.argv, "--version", "-V") or sys.argv[1] == "version":
        print(f"impact-engine {__version__}")
        return

    command = sys.argv[1]

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

    cfg = _load_and_merge_config(project_path, sys.argv)

    max_depth = cfg.get("max_depth", 3)
    max_children = cfg.get("max_children", 12)
    changed_only = cfg.get("changed_only", False)
    summary_json = cfg.get("json_output", False)
    summary_limit = cfg.get("limit", 10)

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

    elif command == "complexity":
        complexity_command(project_path, json_output=summary_json, limit=summary_limit)

    elif command == "mermaid":
        output = _get_flag_value(sys.argv, "--output", "-o")
        show_changed = _has_flag(sys.argv, "--changed", "-c")
        mermaid_command(project_path, output_file=output, show_changed=show_changed)

    elif command == "sarif":
        output = _get_flag_value(sys.argv, "--output", "-o")
        sarif_command(project_path, output_file=output)

    elif command == "compare":
        base_ref = _get_flag_value(sys.argv, "--base", default="main") or "main"
        compare_command(project_path, base_ref=base_ref, json_output=summary_json)

    elif command == "cycles":
        cycles_command(project_path, json_output=summary_json)

    elif command == "watch":
        watch_command(project_path, max_depth=max_depth, max_children=max_children)

    else:
        print(f"Unknown command: {command}")
        print("Commands: analyze, graph, summary, impact, diff, complexity,")
        print("          mermaid, sarif, compare, cycles, version, watch")


if __name__ == "__main__":
    main()
