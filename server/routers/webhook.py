from __future__ import annotations

import hashlib
import hmac
import json
import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

router = APIRouter(prefix="/webhook", tags=["webhook"])


def _verify_signature(payload: bytes, signature_header: str | None) -> bool:
    if not GITHUB_WEBHOOK_SECRET:
        return True
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def _verify_api_key(request: Request) -> bool:
    api_keys_env = os.getenv("ANALYZER_API_KEYS", "")
    if not api_keys_env:
        return True
    valid_keys = set(k.strip() for k in api_keys_env.split(",") if k.strip())
    if not valid_keys:
        return True
    auth = request.headers.get("Authorization", "")
    return auth.startswith("Bearer ") and auth[len("Bearer "):] in valid_keys


@router.post("/github")
async def github_webhook(request: Request):
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured")

    payload_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not _verify_signature(payload_bytes, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    if not _verify_api_key(request):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = request.headers.get("X-GitHub-Event")
    if event == "pull_request":
        action = payload.get("action")
        if action in ("opened", "synchronize"):
            try:
                handle_pr_webhook(payload)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse({"status": "ok"})


def handle_pr_webhook(payload: dict) -> None:
    from core.extractor import extract_project_dependencies
    from core.graph_builder import build_graph
    from core.traversal import get_impact as compute_impact
    from core.analyzer import calculate_risk
    from core.explainer import explain_impact
    from core.report_generator import generate_pr_report
    from core.git_analyzer import get_changed_functions
    from core.runtime_paths import get_project_root

    repo = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]
    project_root = get_project_root()

    deps = extract_project_dependencies(project_root)
    graph = build_graph(deps)
    changed_funcs = list(get_changed_functions(deps, ref=None))

    impact_data: list[dict] = []
    for func in changed_funcs:
        impacted = list(compute_impact(graph, func))
        risk = calculate_risk(graph, func)
        explanation = explain_impact(graph, func, set(impacted))
        impact_data.append({
            "function": func,
            "impact": impacted,
            "risk": risk,
            "explanation": explanation,
        })

    report = generate_pr_report(changed_funcs, impact_data)
    _post_comment(repo, pr_number, report)


def _post_comment(repo: str, pr_number: int, report: str) -> None:
    import requests

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    data = {"body": f"```\n{report}\n```"}

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to post GitHub comment: {e}", file=__import__("sys").stderr)
