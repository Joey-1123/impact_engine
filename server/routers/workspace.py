from __future__ import annotations

from fastapi import APIRouter

from server.schemas import WorkspaceResponse

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("", response_model=WorkspaceResponse)
async def get_workspace() -> WorkspaceResponse:
    from core.workspace import load_workspace_config
    config = load_workspace_config(".")
    if config is None:
        return WorkspaceResponse()

    return WorkspaceResponse(
        repos=[{"path": r.path, "name": r.name, "tags": r.tags} for r in config.repos],
        workspace_root=config.workspace_root,
    )


@router.get("/graph", response_model=dict)
async def get_system_graph() -> dict:
    from core.workspace import load_workspace_config, build_system_graph
    config = load_workspace_config(".")
    if config is None:
        return {"nodes": [], "edges": []}
    g = build_system_graph(config)
    return {
        "nodes": [{"id": n, **d} for n, d in g.nodes(data=True)],
        "edges": [{"source": u, "target": v, **d} for u, v, d in g.edges(data=True)],
    }


@router.get("/conformance", response_model=list[dict])
async def get_conformance() -> list[dict]:
    from core.workspace import load_workspace_config, build_system_graph, check_conformance
    config = load_workspace_config(".")
    if config is None:
        return []
    g = build_system_graph(config)
    return check_conformance(g, [])
