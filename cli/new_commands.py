from __future__ import annotations

import json
import os
from pathlib import Path

from core.health import score_file, compute_kpis


def _run_analysis(project_path: str) -> tuple:
    from core.extractor import extract_project_dependencies_rich
    from core.graph_builder import build_graph
    from core.git_analyzer import get_changed_functions
    from core.detector import find_entry_points
    from core.analyzer import find_dead_code
    from core.detector import find_cycles as _find_cycles

    deps, linenos, complexities = extract_project_dependencies_rich(project_path)
    graph = build_graph(deps)
    changed_funcs = get_changed_functions(deps)
    entry_points = find_entry_points(graph)
    dead_nodes = find_dead_code(graph, entry_points)
    cycles = _find_cycles(graph)
    return deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities


def health_command(project_path: str, json_output: bool = False) -> None:
    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path)
    findings: list = []
    for node in graph.nodes():
        fpath = node.split("::")[0] if "::" in node else node
        score_file(fpath, complexities.get(node, 1), len(list(graph.successors(node))), findings)
    kpis = compute_kpis([], findings)
    if json_output:
        print(json.dumps({"findings": len(findings), "kpis": kpis}, indent=2))
    else:
        print(f"Findings: {len(findings)}")
        for k, v in kpis.items():
            print(f"  {k}: {v:.2f}")


def knowledge_graph_command(project_path: str) -> None:
    from cli.main import _run_analysis
    from core.graph.kg import build_knowledge_graph_skeleton

    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path)
    kg = build_knowledge_graph_skeleton(graph, complexities=complexities, entry_points=list(entry_points)[:5])
    print(f"Knowledge Graph: {len(kg.nodes)} nodes, {len(kg.edges)} edges")
    print(f"Layers: {kg.layers}")
    print(f"Fingerprint: {kg.fingerprint}")
    if kg.tour:
        print("Tour:")
        for step in kg.tour:
            print(f"  {step['title']} -> {step['target']}")


def decisions_command(project_path: str, source: str = "pr") -> None:
    from core.decisions import extract_pr_decisions, extract_adrs, mine_changelog_decisions

    all_decisions = []
    if source == "pr":
        import subprocess
        result = subprocess.run(["git", "log", "--oneline", "-20"], capture_output=True, text=True, cwd=project_path)
        for line in result.stdout.strip().splitlines():
            all_decisions.extend(extract_pr_decisions(line))
    elif source == "adr":
        adr_dir = Path(project_path) / "docs" / "adr"
        if adr_dir.is_dir():
            all_decisions = extract_adrs(adr_dir)
    elif source == "changelog":
        for name in ("CHANGELOG.md", "CHANGELOG.rst"):
            cl_path = Path(project_path) / name
            if cl_path.exists():
                all_decisions = mine_changelog_decisions(cl_path)
                break
    print(f"Decisions: {len(all_decisions)}")
    for d in all_decisions[:10]:
        print(f"  [{d.status}] {d.title} (conf={d.confidence:.2f})")


def cost_command(types_str: str, count: int, model: str) -> None:
    from core.cost_estimator import estimate_cost

    types = [t.strip() for t in types_str.split(",") if t.strip()]
    est = estimate_cost(types, count=count, model=model)
    print(f"Model: {est.model}")
    print(f"Input tokens: {est.total_input_tokens}")
    print(f"Output tokens: {est.total_output_tokens}")
    print(f"Estimated cost: ${est.estimated_cost_usd:.4f}")


def duplication_command(project_path: str, window: int = 50) -> None:
    from core.health.duplication import find_clones

    file_sources: dict[str, str] = {}
    for f in Path(project_path).rglob("*.py"):
        if ".venv" in str(f) or "__pycache__" in str(f):
            continue
        file_sources[str(f)] = f.read_text(encoding="utf-8")
    report = find_clones(file_sources, window=window)
    print(f"Clone pairs: {report.total_clones}")
    print(f"Duplicated lines: {report.duplicated_lines}")
    for p in report.pairs[:10]:
        print(f"  {p.file_a}:{p.start_a} <-> {p.file_b}:{p.start_b}  len={p.length}  sim={p.similarity:.2f}")


def serve_command(host: str, port: int) -> None:
    import uvicorn
    from server.app import create_app

    app = create_app()
    print(f"Starting Impact Engine server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


def mcp_command(port: int) -> None:
    import uvicorn
    from server.mcp_server import create_mcp_server

    mcp = create_mcp_server()
    print(f"Starting MCP server on port {port}")
    mcp.run(port=port)
