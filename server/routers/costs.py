from __future__ import annotations

from fastapi import APIRouter, Query

from server.schemas import CostResponse

router = APIRouter(prefix="/api/repos/{repo_id}", tags=["costs"])


@router.get("/costs", response_model=CostResponse)
async def estimate_costs(
    repo_id: str,
    page_types: str = Query("file_summary", description="Comma-separated page types"),
    count: int = Query(1, description="Number of items"),
    model: str = Query("claude-sonnet-4-6", description="Model name"),
) -> CostResponse:
    from core.cost_estimator import estimate_cost

    types = [t.strip() for t in page_types.split(",") if t.strip()]
    est = estimate_cost(types, count=count, model=model)

    return CostResponse(
        model=est.model,
        estimated_cost_usd=est.estimated_cost_usd,
        total_input_tokens=est.total_input_tokens,
        total_output_tokens=est.total_output_tokens,
        breakdown=est.breakdown,
    )
