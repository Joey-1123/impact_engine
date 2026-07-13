from __future__ import annotations

from fastapi import APIRouter, Query, Request

from server.repo_worker import analyze_repo
from server.schemas import HealthScoreResponse

router = APIRouter(prefix="/api/repos/{repo_id}", tags=["health"])


@router.get("/health-score", response_model=HealthScoreResponse)
async def get_health_score(
    repo_id: str,
    request: Request,
    mode: str = Query("standard", description="Scoring mode: standard, fast, essential"),
) -> HealthScoreResponse:
    app_repo = request.app.state.repo_path
    repo_path = app_repo or repo_id
    data = await analyze_repo(repo_path)

    graph = data["graph"]
    complexities = data["complexities"]
    findings: list[dict] = []
    total_defect = 0.0
    total_maint = 0.0
    total_perf = 0.0
    count = 0

    for node in graph.nodes():
        ccn = complexities.get(node, 1)
        if ccn > 10:
            findings.append({"node": node, "type": "complex_method", "severity": "high", "ccn": ccn})
            total_defect += 0.5
            total_maint += 0.3
        if ccn > 20:
            findings.append({"node": node, "type": "brain_method", "severity": "critical", "ccn": ccn})
            total_defect += 1.0
            total_maint += 0.5
        count += 1

    file_count = max(count, 1)
    defect = max(1.0, 10.0 - total_defect / file_count * 10)
    maint = max(1.0, 10.0 - total_maint / file_count * 10)
    perf = 10.0
    overall = round((defect + maint + perf) / 3, 2)

    return HealthScoreResponse(
        overall=overall,
        defect=round(defect, 2),
        maintainability=round(maint, 2),
        performance=round(perf, 2),
        findings_count=len(findings),
        kpis={
            "average_health": overall,
            "file_count": file_count,
            "finding_count": len(findings),
        },
    )


@router.get("/findings", response_model=list[dict])
async def get_findings(
    repo_id: str,
    request: Request,
    category: str = Query("", description="Filter by category"),
    severity: str = Query("", description="Filter by severity: critical, high, medium, low"),
) -> list[dict]:
    app_repo = request.app.state.repo_path
    repo_path = app_repo or repo_id
    data = await analyze_repo(repo_path)

    graph = data["graph"]
    complexities = data["complexities"]
    findings: list[dict] = []

    for node in graph.nodes():
        ccn = complexities.get(node, 1)
        findings.append({
            "node": node,
            "type": "complex_method" if ccn > 10 else "ok",
            "severity": "high" if ccn > 10 else ("critical" if ccn > 20 else "low"),
            "ccn": ccn,
            "file": node.split("::")[0] if "::" in node else node,
        })

    if category:
        findings = [f for f in findings if f["type"] == category]
    if severity:
        findings = [f for f in findings if f["severity"] == severity]

    return findings
