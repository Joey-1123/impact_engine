from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query, Request
import networkx as nx

from server.repo_worker import analyze_repo
from server.schemas import GraphResponse

router = APIRouter(prefix="/api/repos/{repo_id}", tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    repo_id: str,
    request: Request,
    entry_points: str = Query("", description="Comma-separated entry point symbols"),
) -> GraphResponse:
    from core.graph.kg import build_knowledge_graph_skeleton

    app_repo = request.app.state.repo_path
    repo_path = app_repo or repo_id
    data = await analyze_repo(repo_path)

    graph = data["graph"]
    complexities = data["complexities"]
    entry_pts = [ep.strip() for ep in entry_points.split(",") if ep.strip()]
    if not entry_pts:
        entry_pts = list(data["entry_points"])[:5]

    kg = build_knowledge_graph_skeleton(
        graph,
        complexities=complexities,
        entry_points=entry_pts,
    )

    return GraphResponse(
        nodes=[{"id": n.id, "type": n.type, "file_path": n.file_path, "label": n.label, "layer": n.layer, "pagerank": n.pagerank, "community": n.community, "complexity": n.complexity} for n in kg.nodes],
        edges=[{"source": e.source, "target": e.target, "type": e.type} for e in kg.edges],
        layers=kg.layers,
        fingerprint=kg.fingerprint,
    )


@router.get("/layers", response_model=list[str])
async def get_layers(repo_id: str, request: Request) -> list[str]:
    app_repo = request.app.state.repo_path
    repo_path = app_repo or repo_id
    data = await analyze_repo(repo_path)
    return list(data["layers"].keys())
