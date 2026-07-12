from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolEntry:
    fn: Callable[..., Any]
    name: str
    default: bool = True
    requires_workspace: bool = False


class MCPToolRegistry:
    def __init__(self) -> None:
        self._entries: list[ToolEntry] = []
        self._applied_to: list[Any] = []

    def register(
        self, default: bool = True, requires_workspace: bool = False
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self._entries.append(
                ToolEntry(
                    fn=fn,
                    name=fn.__name__,
                    default=default,
                    requires_workspace=requires_workspace,
                )
            )
            return fn
        return decorator

    tool = register

    def apply(self, mcp: Any, middleware: Callable | None = None) -> None:
        from mcp.server.fastmcp import FastMCP

        if not isinstance(mcp, FastMCP):
            return
        if mcp in self._applied_to:
            return
        for entry in self._entries:
            fn = entry.fn
            if middleware:
                fn = middleware(fn)
            mcp.tool(name=entry.name)(fn)
        self._applied_to.append(mcp)

    def reset(self) -> None:
        self._entries.clear()
        self._applied_to.clear()

    def tools(self) -> list[ToolEntry]:
        return list(self._entries)

    def entries(self) -> list[ToolEntry]:
        return list(self._entries)


mcp_tool_registry = MCPToolRegistry()
