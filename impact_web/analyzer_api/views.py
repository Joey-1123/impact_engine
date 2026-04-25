from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
from django.shortcuts import render
from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.analyzer import calculate_risk, find_dead_code

BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "tests"
)

@api_view(["GET"])
def analyze(request):
    deps = extract_project_dependencies(BASE_DIR)
    graph = build_graph(deps)

    entry_points = [n for n in graph.nodes() if n.endswith("::main")]
    if not entry_points:
        entry_points = [n for n in graph.nodes() if graph.in_degree(n) == 0]

    dead = find_dead_code(graph, entry_points)

    # NEW: attach risk to each node
    nodes_with_risk = []
    for node in graph.nodes():
        risk = calculate_risk(graph, node)
        nodes_with_risk.append({
            "id": node,
            "risk": risk
        })

    return Response({
        "nodes": nodes_with_risk,
        "edges": list(graph.edges()),
        "dead_code": dead,
    })


@api_view(["GET"])
def impact(request):
    target = request.GET.get("function", "a")

    deps = extract_project_dependencies(BASE_DIR)
    graph = build_graph(deps)

    matches = [n for n in graph.nodes if n.endswith(f"::{target}")]

    result = []

    for m in matches:
        impacted = list(get_impact(graph, m))
        risk = calculate_risk(graph, m)

        result.append({
            "function": m,
            "impact": impacted,
            "risk": risk
        })

    return Response(result)
def home(request):
    return render(request, "index.html")