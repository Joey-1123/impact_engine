from __future__ import annotations

from fastapi import APIRouter, Query

from server.schemas import DecisionResponse

router = APIRouter(prefix="/api/repos/{repo_id}", tags=["decisions"])


@router.get("/decisions", response_model=DecisionResponse)
async def get_decisions(
    repo_id: str,
    status: str = Query("", description="Filter by status: active, deprecated, superseded"),
    limit: int = Query(50, description="Max decisions to return"),
) -> DecisionResponse:
    return DecisionResponse(decisions=[], total=0)
