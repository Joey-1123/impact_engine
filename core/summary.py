from core.analyzer import calculate_risk
from core.version import __version__


def build_analysis_summary(graph, changed_nodes=None, dead_nodes=None, limit=10):
    """
    Build a compact, decision-oriented summary of the current graph.
    """
    changed_set = set(changed_nodes or [])
    dead_nodes = list(dead_nodes or [])

    ranked_nodes = []
    for node in graph.nodes():
        risk = calculate_risk(graph, node)
        ranked_nodes.append({
            "node": node,
            "risk": risk,
            "outgoing": graph.out_degree(node),
            "incoming": graph.in_degree(node),
            "changed": node in changed_set,
        })

    ranked_nodes.sort(
        key=lambda item: (
            item["risk"],
            item["outgoing"],
            item["incoming"],
            item["node"],
        ),
        reverse=True,
    )

    changed_hotspots = [
        item for item in ranked_nodes if item["changed"]
    ][:limit]

    return {
        "counts": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "changed": len(changed_set),
            "dead": len(dead_nodes),
        },
        "top_hotspots": ranked_nodes[:limit],
        "changed_hotspots": changed_hotspots,
        "dead_nodes": dead_nodes[:limit],
    }


def build_analysis_summary_payload(graph, changed_nodes=None, dead_nodes=None, limit=10):
    """
    JSON-friendly summary payload for CI/PR bots.
    """
    summary = build_analysis_summary(
        graph,
        changed_nodes=changed_nodes,
        dead_nodes=dead_nodes,
        limit=limit,
    )

    return {
        "version": __version__,
        "counts": summary["counts"],
        "top_hotspots": summary["top_hotspots"],
        "changed_hotspots": summary["changed_hotspots"],
        "dead_nodes": summary["dead_nodes"],
    }
