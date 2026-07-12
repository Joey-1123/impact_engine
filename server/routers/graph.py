from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query

from server.schemas import GraphResponse

router = APIRouter(prefix="/api/repos/{repo_id}", tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    repo_id: str,
    entry_points: str = Query("", description="Comma-separated entry point symbols"),
) -> GraphResponse:
    from core.graph.kg import build_knowledge_graph_skeleton
    import networkx as nx

    g = nx.DiGraph()
    eps = [ep.strip() for ep in entry_points.split(",") if ep.strip()]

    return GraphResponse(
        nodes=[],
        edges=[],
        layers=[],
        fingerprint="",
    )


@router.get("/layers", response_model=list[str])
async def get_layers(repo_id: str) -> list[str]:
    return []
