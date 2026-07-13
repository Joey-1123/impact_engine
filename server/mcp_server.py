from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from core.registry import mcp_tool_registry


def create_mcp_server(name: str = "impact-engine") -> FastMCP:
    mcp = FastMCP(name)
    mcp_tool_registry.apply(mcp)
    return mcp


@mcp_tool_registry.register()
async def get_overview(repo_path: str) -> str:
    from core.layer_inference import infer_layer

    path = Path(repo_path)
    if not path.is_dir():
        return f"Repository path not found: {repo_path}"

    layers: dict[str, int] = {}
    total_files = 0
    for f in path.rglob("*.py"):
        if ".venv" in str(f) or "__pycache__" in str(f):
            continue
        total_files += 1
        layer = infer_layer(str(f))
        layers[layer] = layers.get(layer, 0) + 1

    return (
        f"Overview of {repo_path}\n"
        f"Total Python files: {total_files}\n"
        f"Layers: {layers}\n"
    )


@mcp_tool_registry.register()
async def get_health(repo_path: str) -> str:
    return f"Health analysis not yet implemented for {repo_path}"


@mcp_tool_registry.register()
async def get_graph(repo_path: str) -> str:
    return f"Graph analysis not yet implemented for {repo_path}"


@mcp_tool_registry.register()
async def list_tools() -> str:
    from core.registry import mcp_tool_registry

    registry = mcp_tool_registry
    tool_list = [f"- {e.name}: {e.fn.__doc__ or 'No description'}" for e in registry.entries()]
    return "Available tools:\n" + "\n".join(tool_list)
