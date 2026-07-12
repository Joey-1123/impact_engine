from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx


@dataclass
class KnowledgeGraphNode:
    id: str
    type: str = "file"
    file_path: str = ""
    label: str = ""
    layer: str = ""
    pagerank: float = 0.0
    community: int = -1
    complexity: str = "simple"


@dataclass
class KnowledgeGraphEdge:
    source: str
    target: str
    type: str = "imports"


@dataclass
class KnowledgeGraphResult:
    nodes: list[KnowledgeGraphNode] = field(default_factory=list)
    edges: list[KnowledgeGraphEdge] = field(default_factory=list)
    layers: list[str] = field(default_factory=list)
    tour: list[dict[str, str]] = field(default_factory=list)
    modules: list[dict[str, Any]] = field(default_factory=list)
    fingerprint: str = ""


def build_knowledge_graph_skeleton(
    graph: nx.DiGraph,
    base_dir: Path | None = None,
    complexities: dict[str, int] | None = None,
    entry_points: list[str] | None = None,
) -> KnowledgeGraphResult:
    complexities = complexities or {}
    entry_points = entry_points or []

    try:
        pr = nx.pagerank(graph)
    except (ImportError, NotImplementedError):
        pr = {n: 1.0 / max(graph.number_of_nodes(), 1) for n in graph.nodes()}

    communities: dict[str, int] = {}
    try:
        from networkx.algorithms.community import greedy_modularity_communities
        undirected = graph.to_undirected()
        community_gen = greedy_modularity_communities(undirected)
        for cid, members in enumerate(community_gen):
            for m in members:
                communities[m] = cid
    except (ImportError, ValueError, Exception):
        for i, node in enumerate(graph.nodes()):
            communities[node] = i

    file_layers: dict[str, str] = {}
    for node in graph.nodes():
        fpath = node.split("::")[0] if "::" in node else node
        if fpath not in file_layers:
            try:
                from core.layer_inference import infer_layer
                file_layers[fpath] = infer_layer(fpath)
            except ImportError:
                file_layers[fpath] = "Application"

    kg_nodes: list[KnowledgeGraphNode] = []
    seen_paths: set[str] = set()

    sorted_nodes = sorted(graph.nodes(), key=lambda n: pr.get(n, 0), reverse=True)

    for node in sorted_nodes[:200]:
        fpath = node.split("::")[0] if "::" in node else node
        ccn = complexities.get(node, 1)
        comp = "complex" if ccn > 10 else "moderate" if ccn > 5 else "simple"

        if fpath not in seen_paths:
            seen_paths.add(fpath)
            kg_nodes.append(
                KnowledgeGraphNode(
                    id=fpath,
                    type="file",
                    file_path=fpath,
                    label=Path(fpath).name,
                    layer=file_layers.get(fpath, "Application"),
                    pagerank=pr.get(node, 0),
                    community=communities.get(node, -1),
                    complexity=comp,
                )
            )

        pr_threshold = sorted(pr.values(), reverse=True)[min(50, len(pr) - 1)] if pr else 0
        if pr.get(node, 0) >= pr_threshold:
            kg_nodes.append(
                KnowledgeGraphNode(
                    id=node,
                    type="function",
                    file_path=fpath,
                    label=node.split("::")[-1] if "::" in node else node,
                    layer=file_layers.get(fpath, "Application"),
                    pagerank=pr.get(node, 0),
                    community=communities.get(node, -1),
                    complexity=comp,
                )
            )

    node_set = {n.id for n in kg_nodes}
    kg_edges: list[KnowledgeGraphEdge] = []
    for u, v in graph.edges():
        fu = u.split("::")[0] if "::" in u else u
        fv = v.split("::")[0] if "::" in v else v
        if fu in node_set and fv in node_set and fu != fv:
            kg_edges.append(KnowledgeGraphEdge(source=fu, target=fv, type="imports"))
        if u in node_set and v in node_set and u != v:
            kg_edges.append(KnowledgeGraphEdge(source=u, target=v, type="depends_on"))

    layers_set: set[str] = set()
    for n in kg_nodes:
        if n.layer:
            layers_set.add(n.layer)
    from core.layer_inference import compute_layer_order
    file_layer_map = {n.file_path: n.layer for n in kg_nodes}
    import_edges = [(u, v) for u, v in graph.edges() if u in pr and v in pr]
    ordered_layers = compute_layer_order(file_layer_map, import_edges)

    tour_steps: list[dict[str, str]] = []
    if entry_points:
        for ep in entry_points[:5]:
            fpath = ep.split("::")[0] if "::" in ep else ep
            tour_steps.append({
                "title": f"Entry point: {ep}",
                "target": fpath,
                "reason": "Top-level entry point into the codebase",
            })

    return KnowledgeGraphResult(
        nodes=kg_nodes,
        edges=kg_edges,
        layers=ordered_layers,
        tour=tour_steps,
        fingerprint=str(hash(frozenset(graph.nodes()))),
    )
