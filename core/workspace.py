from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


@dataclass
class RepoEntry:
    path: str
    name: str = ""
    tags: list[str] = field(default_factory=list)
    default_branch: str = "main"


@dataclass
class WorkspaceConfig:
    repos: list[RepoEntry] = field(default_factory=list)
    workspace_root: str = ""


@dataclass
class SystemEdge:
    source: str
    target: str
    kind: str = "imports"
    confidence: float = 1.0


SystemGraph = nx.DiGraph


def load_workspace_config(path: str | Path) -> WorkspaceConfig | None:
    if yaml is None:
        return None
    path = Path(path)
    candidates = [
        path / "impact-workspace.yaml",
        path / "impact-workspace.yml",
        path / ".impactrc",
    ]
    for candidate in candidates:
        if candidate.exists():
            raw = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            if not raw or "repos" not in raw:
                return None
            repos = []
            for r in raw.get("repos", []):
                if isinstance(r, str):
                    repos.append(RepoEntry(path=r, name=Path(r).name))
                elif isinstance(r, dict):
                    repos.append(
                        RepoEntry(
                            path=r.get("path", ""),
                            name=r.get("name", Path(r.get("path", "")).name),
                            tags=r.get("tags", []),
                            default_branch=r.get("default_branch", "main"),
                        )
                    )
            return WorkspaceConfig(
                repos=repos,
                workspace_root=str(path),
            )
    return None


def build_system_graph(config: WorkspaceConfig) -> SystemGraph:
    g: nx.DiGraph = nx.DiGraph()
    for repo in config.repos:
        repo_id = repo.name or os.path.basename(repo.path)
        g.add_node(repo_id, type="repo", path=repo.path, tags=repo.tags)
    return g


def add_contract_edge(
    graph: SystemGraph,
    source: str,
    target: str,
    kind: str = "http",
    confidence: float = 1.0,
) -> None:
    if source in graph and target in graph:
        graph.add_edge(source, target, kind=kind, confidence=confidence)


def check_conformance(
    graph: SystemGraph,
    rules: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    rules = rules or []
    for rule in rules:
        forbidden = rule.get("forbidden_edges", [])
        for src, dst, data in graph.edges(data=True):
            edge_kind = data.get("kind", "")
            for f_src, f_dst, f_kind in forbidden:
                if src == f_src and dst == f_dst and edge_kind == f_kind:
                    violations.append({
                        "rule": rule.get("name", "unknown"),
                        "source": src,
                        "target": dst,
                        "kind": edge_kind,
                        "message": f"Forbidden edge: {src} -> {dst} ({edge_kind})",
                    })
    return violations
