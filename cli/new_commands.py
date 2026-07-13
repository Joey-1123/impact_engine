from __future__ import annotations

import json
import os
from pathlib import Path

from core.health import (
    HealthFileMetricData,
    Severity,
    attach_impacts,
    compute_kpis,
    score_file,
)
from core.health.biomarkers import BiomarkerResult


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
    metrics: list = []
    for node in graph.nodes():
        func_results: list[BiomarkerResult] = []
        fpath = node.split("::")[0] if "::" in node else node
        ccn = complexities.get(node, 1)
        if ccn > 10:
            func_results.append(
                BiomarkerResult(
                    biomarker_type="complex_method",
                    severity=Severity.HIGH,
                    function_name=node,
                    details={"cyclomatic_complexity": ccn},
                )
            )
        if ccn > 20:
            func_results.append(
                BiomarkerResult(
                    biomarker_type="brain_method",
                    severity=Severity.CRITICAL,
                    function_name=node,
                    details={"cyclomatic_complexity": ccn},
                )
            )
        if func_results:
            scores, deductions = score_file(func_results)
            impacted = attach_impacts(func_results, deductions)
            findings.extend(impacted)
        else:
            scores = {"defect": 10.0, "maintainability": 10.0, "performance": 10.0}
        metrics.append(
            HealthFileMetricData(
                file_path=fpath,
                score=scores.get("defect", 10.0) or 10.0,
                max_ccn=ccn,
                max_nesting=0,
                nloc=ccn * 10,
                defect_score=scores.get("defect"),
                maintainability_score=scores.get("maintainability"),
                performance_score=scores.get("performance"),
            )
        )
    hotspot_paths = {m.file_path for m in metrics if m.score < 7.0}
    kpis = compute_kpis(metrics, hotspot_paths)
    if json_output:
        print(json.dumps({"findings": len(findings), "kpis": kpis}, indent=2))
    else:
        print(f"Findings: {len(findings)}")
        print(f"Files analyzed: {len(metrics)}")
        for k, v in kpis.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.2f}")
            else:
                print(f"  {k}: {v}")


def knowledge_graph_command(project_path: str, json_output: bool = False) -> None:
    from core.graph.kg import build_knowledge_graph_skeleton

    deps, graph, changed_funcs, entry_points, dead_nodes, cycles, linenos, complexities = _run_analysis(project_path)
    kg = build_knowledge_graph_skeleton(graph, complexities=complexities, entry_points=list(entry_points)[:5])
    if json_output:
        import json as _json
        print(_json.dumps({
            "nodes": len(kg.nodes),
            "edges": len(kg.edges),
            "layers": kg.layers,
            "fingerprint": kg.fingerprint,
            "tour": kg.tour,
        }, indent=2))
    else:
        print(f"Knowledge Graph: {len(kg.nodes)} nodes, {len(kg.edges)} edges")
        print(f"Layers: {kg.layers}")
        print(f"Fingerprint: {kg.fingerprint}")
        if kg.tour:
            print("Tour:")
            for step in kg.tour:
                print(f"  {step['title']} -> {step['target']}")


def decisions_command(project_path: str, source: str = "pr", json_output: bool = False) -> None:
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
    if json_output:
        import json as _json
        print(_json.dumps({
            "total": len(all_decisions),
            "decisions": [
                {
                    "title": d.title,
                    "status": d.status,
                    "confidence": d.confidence,
                    "source": d.source,
                    "rationale": d.rationale,
                }
                for d in all_decisions
            ],
        }, indent=2))
    else:
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


def duplication_command(project_path: str, window: int = 50, json_output: bool = False) -> None:
    from core.health.duplication import find_clones

    file_sources: dict[str, str] = {}
    for f in Path(project_path).rglob("*.py"):
        if ".venv" in str(f) or "__pycache__" in str(f):
            continue
        file_sources[str(f)] = f.read_text(encoding="utf-8")
    report = find_clones(file_sources, window=window)
    if json_output:
        import json as _json
        pairs = [
            {
                "file_a": p.file_a,
                "file_b": p.file_b,
                "start_a": p.start_a,
                "start_b": p.start_b,
                "length": p.length,
                "similarity": p.similarity,
            }
            for p in report.pairs[:50]
        ]
        print(_json.dumps({
            "total_clones": report.total_clones,
            "duplicated_lines": report.duplicated_lines,
            "pairs": pairs,
        }, indent=2))
    else:
        print(f"Clone pairs: {report.total_clones}")
        print(f"Duplicated lines: {report.duplicated_lines}")
        for p in report.pairs[:10]:
            print(f"  {p.file_a}:{p.start_a} <-> {p.file_b}:{p.start_b}  len={p.length}  sim={p.similarity:.2f}")


def serve_command(host: str, port: int, project_path: str = "") -> None:
    import uvicorn
    from server.app import create_app

    app = create_app(repo_path=project_path)
    print(f"Starting Impact Engine server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


def mcp_command(port: int) -> None:
    import uvicorn
    from server.mcp_server import create_mcp_server

    mcp = create_mcp_server()
    app = mcp.sse_app()
    print(f"Starting MCP server on port {port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
