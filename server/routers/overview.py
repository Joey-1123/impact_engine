from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.params import Depends

from server.repo_worker import analyze_repo
from server.schemas import OverviewResponse

router = APIRouter(prefix="/api/repos/{repo_id}", tags=["overview"])


def _resolve_repo_path(repo_id: str, request: Request) -> str:
    app_repo = request.app.state.repo_path
    if app_repo:
        return app_repo
    return repo_id


@router.get("/overview", response_model=OverviewResponse)
async def repo_overview(repo_id: str, request: Request) -> OverviewResponse:
    repo_path = _resolve_repo_path(repo_id, request)
    data = await analyze_repo(repo_path)
    return OverviewResponse(
        total_files=data["total_files"],
        total_functions=data["total_functions"],
        total_classes=0,
        languages=data["languages"],
        layers=data["layers"],
        health_score=0.0,
    )
