from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from server.repo_worker import analyze_repo

router = APIRouter(prefix="/api/repos/{repo_id}", tags=["impact"])


@router.get("/impact")
async def get_impact(
    repo_id: str,
    request: Request,
    function: str = Query(..., description="Function name to analyze"),
    test_only: bool = Query(False, description="Only show test files"),
):
    from core.traversal import get_impact as compute_impact
    from core.analyzer import calculate_risk
    from core.explainer import explain_impact

    app_repo = request.app.state.repo_path
    repo_path = app_repo or repo_id
    data = await analyze_repo(repo_path)
    graph = data["graph"]

    matches = [n for n in graph.nodes if n.endswith(f"::{function}")]
    if not matches:
        raise HTTPException(status_code=404, detail=f"Function '{function}' not found")

    results: list[dict] = []
    for m in matches:
        impacted_nodes = set(compute_impact(graph, m))

        if test_only:
            impacted_nodes = {n for n in impacted_nodes if n.split("::")[0].startswith("test")}

        risk = calculate_risk(graph, m)
        explanation = explain_impact(graph, m, impacted_nodes)

        results.append({
            "function": m,
            "impact": sorted(impacted_nodes),
            "impact_count": len(impacted_nodes),
            "risk": risk,
            "explanation": explanation,
        })

    return results


@router.get("/timeline")
async def get_timeline(
    repo_id: str,
    request: Request,
):
    from core.git_analyzer import get_changed_functions

    app_repo = request.app.state.repo_path
    repo_path = app_repo or repo_id
    data = await analyze_repo(repo_path)
    graph = data["graph"]
    deps = data["deps"]

    nodes = list(graph.nodes())
    edges = list(graph.edges())

    before_changed = list(get_changed_functions(deps, "HEAD~1"))
    after_changed = list(get_changed_functions(deps, "HEAD"))

    return {
        "nodes": nodes,
        "edges": edges,
        "before": before_changed,
        "after": after_changed,
    }


@router.get("/report")
async def get_report(
    repo_id: str,
    request: Request,
):
    from core.traversal import get_impact as compute_impact
    from core.analyzer import calculate_risk
    from core.explainer import explain_impact
    from core.report_generator import generate_pr_report
    from core.git_analyzer import get_changed_functions

    app_repo = request.app.state.repo_path
    repo_path = app_repo or repo_id
    data = await analyze_repo(repo_path)
    graph = data["graph"]
    deps = data["deps"]

    changed_funcs = list(get_changed_functions(deps, ref=None))

    impact_data: list[dict] = []
    for func in changed_funcs:
        impacted = list(compute_impact(graph, func))
        risk = calculate_risk(graph, func)
        explanation = explain_impact(graph, func, set(impacted))
        impact_data.append({
            "function": func,
            "impact": impacted,
            "risk": risk,
            "explanation": explanation,
        })

    report = generate_pr_report(changed_funcs, impact_data)

    return {
        "report": report,
        "changed_funcs": changed_funcs,
        "impact_data": impact_data,
    }
