from __future__ import annotations

from fastapi import APIRouter, Query

from server.schemas import HealthScoreResponse

router = APIRouter(prefix="/api/repos/{repo_id}", tags=["health"])


@router.get("/health-score", response_model=HealthScoreResponse)
async def get_health_score(
    repo_id: str,
    mode: str = Query("standard", description="Scoring mode: standard, fast, essential"),
) -> HealthScoreResponse:
    return HealthScoreResponse(overall=0.0)


@router.get("/findings", response_model=list[dict])
async def get_findings(
    repo_id: str,
    category: str = Query("", description="Filter by category"),
    severity: str = Query("", description="Filter by severity: critical, high, medium, low"),
) -> list[dict]:
    return []
