# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import hashlib
import hmac
import json
import os
import time
from functools import wraps
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.analyzer import calculate_risk, find_dead_code
from core.git_analyzer import get_changed_functions
from core.explainer import explain_impact
from core.report_generator import generate_pr_report
from core.runtime_paths import get_project_root
from .github_bot import handle_pr

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
API_KEYS = set(k.strip() for k in os.getenv("ANALYZER_API_KEYS", "").split(",") if k.strip())
PROJECT_ROOT = get_project_root()
GRAPH_CACHE = {"deps": None, "graph": None, "mtime": 0, "ttl": 60}


def _get_cached_graph():
    cache_file = os.path.join(PROJECT_ROOT, ".impact_cache_web")
    cache_mtime = os.path.getmtime(cache_file) if os.path.isfile(cache_file) else 0
    if (
        GRAPH_CACHE["graph"] is not None
        and cache_mtime <= GRAPH_CACHE["mtime"]
        and time.time() - GRAPH_CACHE["mtime"] < GRAPH_CACHE["ttl"]
    ):
        return GRAPH_CACHE["deps"], GRAPH_CACHE["graph"]

    deps = extract_project_dependencies(PROJECT_ROOT)
    graph = build_graph(deps)
    GRAPH_CACHE["deps"] = deps
    GRAPH_CACHE["graph"] = graph
    GRAPH_CACHE["mtime"] = time.time()
    return deps, graph


def require_api_key(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not API_KEYS:
            return view_func(request, *args, **kwargs)
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth[len("Bearer "):] not in API_KEYS:
            return JsonResponse({"error": "Invalid or missing API key"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


@api_view(["GET"])
@require_api_key
def analyze(request):
    deps, graph = _get_cached_graph()

    entry_points = [n for n in graph.nodes() if n.endswith("::main")]
    if not entry_points:
        entry_points = [n for n in graph.nodes() if graph.in_degree(n) == 0]

    dead = find_dead_code(graph, entry_points)

    nodes_with_risk = []
    for node in graph.nodes():
        risk = calculate_risk(graph, node)
        nodes_with_risk.append({
            "id": node,
            "risk": risk
        })

    changed_funcs = get_changed_functions(deps, ref=None)

    return Response({
        "nodes": nodes_with_risk,
        "edges": list(graph.edges()),
        "dead_code": dead,
        "changed": changed_funcs
    })


@api_view(["GET"])
@require_api_key
def impact(request):
    target = request.GET.get("function")
    if not target:
        return Response({"error": "Missing 'function' parameter"}, status=400)

    deps, graph = _get_cached_graph()

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
@require_api_key
def timeline(request):
    deps, graph = _get_cached_graph()

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
@require_api_key
def report(request):
    deps, graph = _get_cached_graph()

    changed_funcs = get_changed_functions(deps, ref=None)

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
        if not GITHUB_TOKEN:
            return JsonResponse(
                {"error": "GITHUB_TOKEN is not configured"},
                status=500,
            )

        if GITHUB_WEBHOOK_SECRET:
            signature_header = request.headers.get("X-Hub-Signature-256")
            if not signature_header:
                return JsonResponse(
                    {"error": "Missing X-Hub-Signature-256"},
                    status=400,
                )
            expected = "sha256=" + hmac.new(
                GITHUB_WEBHOOK_SECRET.encode(),
                request.body,
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, signature_header):
                return JsonResponse(
                    {"error": "Invalid signature"},
                    status=403,
                )
        elif API_KEYS:
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer ") or auth[len("Bearer "):] not in API_KEYS:
                return JsonResponse({"error": "Invalid API key"}, status=401)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON payload"},
                status=400,
            )

        event = request.headers.get("X-GitHub-Event")

        if event == "pull_request":
            action = payload.get("action")

            if action in ["opened", "synchronize"]:
                try:
                    handle_pr(payload, GITHUB_TOKEN, project_root=PROJECT_ROOT)
                except Exception as e:
                    return JsonResponse(
                        {"error": str(e)},
                        status=500,
                    )

        GRAPH_CACHE["mtime"] = 0
        return JsonResponse({"status": "ok"})

    return JsonResponse({"error": "invalid"}, status=400)


def home(request):
    return render(request, "index.html")
