from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
from django.shortcuts import render
from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.analyzer import calculate_risk, find_dead_code
from core.git_analyzer import get_changed_functions , get_changed_files
from core.git_analyzer import get_changed_files , map_files_to_functions
from core.explainer import explain_impact
from core.report_generator import generate_pr_report
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .github_bot import handle_pr

GITHUB_TOKEN = "your_token_here"  # ⚠️ replace later with env var

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

    # 🔥 risk per node
    nodes_with_risk = []
    for node in graph.nodes():
        risk = calculate_risk(graph, node)
        nodes_with_risk.append({
            "id": node,
            "risk": risk
        })

    # 🔥 ADD THIS BLOCK (YOU MISSED THIS)
    changed_files = get_changed_files()
    changed_funcs = map_files_to_functions(changed_files, deps)
    commit = request.GET.get("commit", "HEAD")
    changed_funcs = get_changed_functions(deps, commit)
    
    return Response({
        "nodes": nodes_with_risk,
        "edges": list(graph.edges()),
        "dead_code": dead,
        "changed": changed_funcs   # 👈 THIS IS THE KEY
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
        explanation_data = explain_impact(graph, m, impacted)
        result.append({
            "function": m,
            "impact": impacted,
            "risk": risk,
            "explanations": explanation_data
        })

    return Response(result)
@api_view(["GET"])
def timeline(request):
    deps = extract_project_dependencies(BASE_DIR)
    graph = build_graph(deps)

    nodes = list(graph.nodes())
    edges = list(graph.edges())

    before_changed = get_changed_functions(deps, "HEAD~1")
    after_changed = get_changed_functions(deps, "HEAD")

    return Response({
        "nodes": nodes,
        "edges": edges,
        "before": before_changed,
        "after": after_changed
    })
@api_view(["GET"])
def report(request):
    deps = extract_project_dependencies(BASE_DIR)
    graph = build_graph(deps)

    changed_funcs = get_changed_functions(deps)

    impact_data = []

    for func in changed_funcs:
        impacted = list(get_impact(graph, func))
        risk = calculate_risk(graph, func)
        explanation = explain_impact(graph, func, impacted)

        impact_data.append({
            "function": func,
            "impact": impacted,
            "risk": risk,
            "explanation": explanation
        })

    report = generate_pr_report(changed_funcs, impact_data)

    return Response({
        "report": report
    })



@csrf_exempt
def github_webhook(request):
    if request.method == "POST":
        payload = json.loads(request.body)

        event = request.headers.get("X-GitHub-Event")

        if event == "pull_request":
            action = payload.get("action")

            if action in ["opened", "synchronize"]:
                handle_pr(payload, GITHUB_TOKEN)

        return JsonResponse({"status": "ok"})

    return JsonResponse({"error": "invalid"}, status=400)

def home(request):
    return render(request, "index.html")
