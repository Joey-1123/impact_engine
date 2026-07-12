from __future__ import annotations

from fastapi import APIRouter

from server.schemas import OverviewResponse

router = APIRouter(prefix="/api/repos/{repo_id}", tags=["overview"])


@router.get("/overview", response_model=OverviewResponse)
async def repo_overview(repo_id: str) -> OverviewResponse:
    return OverviewResponse(total_files=0, total_functions=0, total_classes=0)
