# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import argparse
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
from core.html_exporter import export_html


def safe_print(json_output, *args, **kwargs):
    if not json_output:
        print(*args, **kwargs)


def _resolve_project_path(args):
    path = getattr(args, 'project_path', None) or getattr(args, 'project', None)
    if path:
        return os.path.abspath(path)
    return os.getcwd()


def _load_and_merge_config(project_path, args):
    config = load_config(project_path)
    cli_args = {
        "max_depth": getattr(args, 'depth', None) or config.get("max_depth", 3),
        "max_children": getattr(args, 'children', None) or config.get("max_children", 12),
        "limit": getattr(args, 'limit', None) or config.get("limit", 10),
        "json_output": getattr(args, 'json_output', False) or config.get("json_output", False),
        "changed_only": getattr(args, 'changed_only', False),
    }
    return merge_config(cli_args, config)


def _run_analysis(project_path, use_cache=True, respect_gitignore=True):
    if use_cache:
        try:
            from core.cache import extract_project_dependencies_cached
            deps, linenos, complexities = extract_project_dependencies_cached(project_path, use_cache=True, respect_gitignore=respect_gitignore)
        except Exception as e:
            print(f"Warning: cache read failed ({e}), falling back to uncached extraction", file=sys.stderr)
            deps, linenos, complexities = extract_project_dependencies_rich(project_path, respect_gitignore=respect_gitignore)
    else:
        deps, linenos, complexities = extract_project_dependencies_rich(project_path, respect_gitignore=respect_gitignore)
    graph = build_graph(deps)
    changed_funcs = get_changed_functions(deps)
    entry_points = find_entry_points(graph)
    dead_nodes = find_dead_code(graph, entry_points)
    cycles = find_cycles(graph)
    return deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities


def analyze_command(project_path, *, max_depth=3, max_children=12, changed_only=False, respect_gitignore=True):
    from core.visualizer import render_terminal_graph, print_complexity_table

    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path, respect_gitignore=respect_gitignore)

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
            print(f"  {' -> '.join(c for c in cycle)}")
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


def graph_command(project_path, *, max_depth=4, max_children=12, changed_only=False, respect_gitignore=True):
    from core.visualizer import render_terminal_graph

    deps = extract_project_dependencies(project_path, respect_gitignore=respect_gitignore)
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


def summary_command(project_path, *, json_output=False, limit=10, respect_gitignore=True):
    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path, respect_gitignore=respect_gitignore)

    summary = build_analysis_summary(
        graph,
        changed_nodes=changed_funcs,
        dead_nodes=dead_nodes,
        limit=limit,
        complexities=complexities,
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


def impact_command(project_path, target, test_only=False, respect_gitignore=True):
    from core.visualizer import print_impact_tree

    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path, respect_gitignore=respect_gitignore)

    matches = [n for n in graph.nodes() if n.endswith(f"::{target}")]

    if not matches:
        print(f"Function '{target}' not found.")
        return

    for match in matches:
        impacted = list(get_impact(graph, match))

        if test_only:
            impacted = [n for n in impacted if n.split("::")[0].startswith("test")]

        print(f"\nImpact Tree for '{match}':")
        if test_only:
            for func in impacted:
                print(f"├── {func}")
            print(f"\nTest impact: {len(impacted)} test(s) affected")
        else:
            print_impact_tree(graph, match)

            risk = calculate_risk(graph, match, complexities=complexities)
            print(f"Risk Score for '{match}': {risk}")


def diff_command(project_path, json_output=False, respect_gitignore=True):
    if not project_path or not os.path.exists(project_path):
        safe_print(json_output, f"Error: path does not exist: {project_path}")
        return

    deps = extract_project_dependencies(project_path, respect_gitignore=respect_gitignore)
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


def complexity_command(project_path, json_output=False, limit=20, respect_gitignore=True):
    from core.visualizer import print_complexity_table, print_complexity_json

    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path, respect_gitignore=respect_gitignore)

    if json_output:
        print(print_complexity_json(complexities, limit=limit))
        return

    print_complexity_table(complexities, limit=limit)


def mermaid_command(project_path, output_file=None, show_changed=False, respect_gitignore=True):
    deps, graph, changed_funcs, *_ = _run_analysis(project_path, respect_gitignore=respect_gitignore)

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


def sarif_command(project_path, output_file=None, respect_gitignore=True):
    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path, respect_gitignore=respect_gitignore)

    sarif = export_sarif(
        graph,
        changed_nodes=changed_funcs,
        dead_nodes=dead_nodes,
        linenos=linenos,
        tool_version=__version__,
    )

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(sarif)
        print(f"Exported to {output_file}")
    else:
        print(sarif)


def compare_command(project_path, base_ref="main", json_output=False, respect_gitignore=True):
    result = compare_branches(project_path, base_ref=base_ref, respect_gitignore=respect_gitignore)

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


def cycles_command(project_path, json_output=False, respect_gitignore=True):
    deps, graph, *_ = _run_analysis(project_path, respect_gitignore=respect_gitignore)
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


def html_command(project_path, output_file=None, respect_gitignore=True):
    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path, respect_gitignore=respect_gitignore)

    max_risk = 0
    for func in changed_funcs:
        risk = calculate_risk(graph, func, complexities=complexities)
        max_risk = max(max_risk, risk)

    html = export_html(
        graph,
        project=os.path.basename(project_path),
        version=__version__,
        changed_nodes=set(changed_funcs),
        dead_nodes=dead_nodes,
        cycles=cycles,
        max_risk=max_risk,
    )

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Exported to {output_file}")
    else:
        print(html)


def precommit_command(project_path, threshold=5, json_output=False, respect_gitignore=True):
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, encoding="utf-8", cwd=project_path,
    )
    staged_files = [f for f in result.stdout.strip().splitlines() if f.endswith(".py")]
    if not staged_files:
        safe_print(json_output, "No staged Python files.")
        return 0

    deps = extract_project_dependencies(project_path, respect_gitignore=respect_gitignore)
    if not deps:
        safe_print(json_output, "No Python files found.")
        return 0

    graph = build_graph(deps)

    changed_funcs = []
    for func in deps.keys():
        func_file = func.split("::")[0]
        if any(os.path.normpath(f) == os.path.normpath(func_file) for f in staged_files):
            changed_funcs.append(func)

    max_risk = 0
    risks = {}
    for func in changed_funcs:
        risk = calculate_risk(graph, func)
        risks[func] = risk
        max_risk = max(max_risk, risk)

    if json_output:
        sys.stdout.write(json.dumps({
            "max_risk": max_risk,
            "threshold": threshold,
            "functions": {k: v for k, v in sorted(risks.items(), key=lambda x: -x[1])},
            "commit_allowed": max_risk <= threshold,
        }, indent=2))
        sys.stdout.flush()
    else:
        print(f"\nPre-commit Impact Check:")
        print(f"  Staged files: {len(staged_files)}")
        print(f"  Changed functions: {len(changed_funcs)}")
        print(f"  Max risk: {max_risk}")
        print(f"  Threshold: {threshold}")
        if max_risk > threshold:
            print(f"\n  FAILED: Max risk ({max_risk}) exceeds threshold ({threshold})")
            for func, risk in sorted(risks.items(), key=lambda x: -x[1]):
                print(f"    - {func} (risk={risk})")
        else:
            print(f"\n  PASSED")

    return 1 if max_risk > threshold else 0


def predict_command(project_path, target, json_output=False, respect_gitignore=True):
    deps, graph, *_ = _run_analysis(project_path, respect_gitignore=respect_gitignore)

    matches = [n for n in graph.nodes() if n.endswith(f"::{target}")]

    if not matches:
        safe_print(json_output, f"Function '{target}' not found.")
        return

    for match in matches:
        impacted = list(get_impact(graph, match))
        risk = len(impacted)
        if json_output:
            sys.stdout.write(json.dumps({
                "function": match,
                "risk": risk,
                "impacted": impacted,
            }, indent=2))
            sys.stdout.flush()
        else:
            print(f"\nWhat-if analysis for '{match}':")
            print(f"  Risk score: {risk}")
            print(f"  Impacted functions ({len(impacted)}):")
            for i in impacted[:20]:
                print(f"    - {i}")
            if len(impacted) > 20:
                print(f"    ... {len(impacted) - 20} more")


def watch_command(project_path, max_depth=3, max_children=12, respect_gitignore=True):
    from core.watcher import watch

    def on_change(changed_files):
        print(f"\n[{len(changed_files)} file(s) changed] Re-running analysis...\n")
        analyze_command(project_path, max_depth=max_depth, max_children=max_children, changed_only=True, respect_gitignore=respect_gitignore)

    print(f"Watching {project_path} for changes... (Ctrl+C to stop)")
    watch(project_path, on_change)


def incremental_watch_command(project_path, max_depth=3, max_children=12, respect_gitignore=True):
    from core.watcher import incremental_watch

    def on_change(changed_files):
        print(f"\n[{len(changed_files)} file(s) changed] Re-running analysis...\n")
        analyze_command(project_path, max_depth=max_depth, max_children=max_children, changed_only=True, respect_gitignore=respect_gitignore)

    print(f"Watching {project_path} for changes... (Ctrl+C to stop)")
    incremental_watch(project_path, on_change)


def main():
    parser = argparse.ArgumentParser(
        prog="impact-engine",
        epilog="Built by Shubham Panchal (Joey) — github.com/Joey-1123",
    )
    parser.add_argument("--version", "-V", action="store_true", help="Show version")
    parser.add_argument("--project", "-p", help="Project path")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    p_analyze = sub.add_parser("analyze", help="Full analysis with tree + complexity + dead code")
    p_analyze.add_argument("--depth", type=int, default=3)
    p_analyze.add_argument("--children", type=int, default=12)
    p_analyze.add_argument("--changed-only", "--focused", action="store_true")

    p_graph = sub.add_parser("graph", help="Terminal dependency graph only")
    p_graph.add_argument("--depth", type=int, default=4)
    p_graph.add_argument("--children", type=int, default=12)
    p_graph.add_argument("--changed-only", "--focused", action="store_true")

    p_summary = sub.add_parser("summary", help="Ranked risk hotspots")
    p_summary.add_argument("--json", "--jsonc", action="store_true", dest="json_output")
    p_summary.add_argument("--limit", type=int, default=10)

    p_impact = sub.add_parser("impact", help="Show what breaks if function changes")
    p_impact.add_argument("function", help="Function name to analyze")
    p_impact.add_argument("--test-only", action="store_true", help="Show only test impact")

    p_diff = sub.add_parser("diff", help="Current working tree changes")
    p_diff.add_argument("--json", "--jsonc", action="store_true", dest="json_output")

    p_complexity = sub.add_parser("complexity", help="Cyclomatic complexity ranking")
    p_complexity.add_argument("--json", "--jsonc", action="store_true", dest="json_output")
    p_complexity.add_argument("--limit", type=int, default=20)

    p_mermaid = sub.add_parser("mermaid", help="Export Mermaid.js diagram")
    p_mermaid.add_argument("--output", "-o", help="Output file")
    p_mermaid.add_argument("--changed", "-c", action="store_true", help="Highlight changed nodes")

    p_sarif = sub.add_parser("sarif", help="Export SARIF for GitHub code scanning")
    p_sarif.add_argument("--output", "-o", help="Output file")

    p_compare = sub.add_parser("compare", help="Risk delta between branches")
    p_compare.add_argument("--base", default="main", help="Base branch")
    p_compare.add_argument("--json", "--jsonc", action="store_true", dest="json_output")

    p_cycles = sub.add_parser("cycles", help="Find circular dependencies")
    p_cycles.add_argument("--json", "--jsonc", action="store_true", dest="json_output")

    p_watch = sub.add_parser("watch", help="Polling watcher")
    p_watch.add_argument("--depth", type=int, default=3)
    p_watch.add_argument("--children", type=int, default=12)

    p_iwatch = sub.add_parser("iwatch", aliases=["incremental-watch"], help="Incremental watcher")
    p_iwatch.add_argument("--depth", type=int, default=3)
    p_iwatch.add_argument("--children", type=int, default=12)

    p_precommit = sub.add_parser("pre-commit", help="Check staged files against risk threshold")
    p_precommit.add_argument("--threshold", "-t", type=int, default=5)
    p_precommit.add_argument("--json", "--jsonc", action="store_true", dest="json_output")

    p_predict = sub.add_parser("predict", help="What-if analysis without git changes")
    p_predict.add_argument("function", help="Function name to predict")
    p_predict.add_argument("--json", "--jsonc", action="store_true", dest="json_output")

    p_html = sub.add_parser("html", help="Interactive D3.js HTML report")
    p_html.add_argument("--output", "-o", help="Output file")

    sub.add_parser("version", help="Print version and exit")
    sub.add_parser("help", help="Print this help message")

    args = parser.parse_args()

    if args.version or args.command == "version":
        print(f"impact-engine {__version__}")
        print("Built by Shubham Panchal (Joey) — github.com/Joey-1123")
        return

    if args.command in (None, "help"):
        parser.print_help()
        return

    project_path = _resolve_project_path(args)

    if not os.path.exists(project_path):
        print(f"Error: path does not exist: {project_path}")
        return

    cfg = _load_and_merge_config(project_path, args)

    max_depth = cfg.get("max_depth", 3)
    max_children = cfg.get("max_children", 12)
    changed_only = cfg.get("changed_only", False)
    summary_json = cfg.get("json_output", False)
    summary_limit = cfg.get("limit", 10)
    respect_gitignore = cfg.get("respect_gitignore", True)

    if args.command == "analyze":
        analyze_command(
            project_path,
            max_depth=max_depth,
            max_children=max_children,
            changed_only=changed_only,
            respect_gitignore=respect_gitignore,
        )

    elif args.command == "graph":
        graph_command(
            project_path,
            max_depth=max_depth,
            max_children=max_children,
            changed_only=changed_only,
            respect_gitignore=respect_gitignore,
        )

    elif args.command == "summary":
        summary_command(
            project_path,
            json_output=summary_json,
            limit=summary_limit,
            respect_gitignore=respect_gitignore,
        )

    elif args.command == "impact":
        impact_command(project_path, args.function, test_only=args.test_only, respect_gitignore=respect_gitignore)

    elif args.command == "diff":
        diff_command(project_path, json_output=summary_json, respect_gitignore=respect_gitignore)

    elif args.command == "complexity":
        complexity_command(project_path, json_output=summary_json, limit=summary_limit, respect_gitignore=respect_gitignore)

    elif args.command == "mermaid":
        mermaid_command(project_path, output_file=args.output, show_changed=args.changed, respect_gitignore=respect_gitignore)

    elif args.command == "sarif":
        sarif_command(project_path, output_file=args.output, respect_gitignore=respect_gitignore)

    elif args.command == "compare":
        compare_command(project_path, base_ref=args.base, json_output=summary_json, respect_gitignore=respect_gitignore)

    elif args.command == "cycles":
        cycles_command(project_path, json_output=summary_json, respect_gitignore=respect_gitignore)

    elif args.command == "watch":
        watch_command(project_path, max_depth=max_depth, max_children=max_children, respect_gitignore=respect_gitignore)

    elif args.command in ("iwatch", "incremental-watch"):
        incremental_watch_command(project_path, max_depth=max_depth, max_children=max_children, respect_gitignore=respect_gitignore)

    elif args.command == "pre-commit":
        exit_code = precommit_command(project_path, threshold=args.threshold, json_output=summary_json, respect_gitignore=respect_gitignore)
        sys.exit(exit_code)

    elif args.command == "predict":
        predict_command(project_path, args.function, json_output=summary_json, respect_gitignore=respect_gitignore)

    elif args.command == "html":
        html_command(project_path, output_file=args.output, respect_gitignore=respect_gitignore)

    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()
