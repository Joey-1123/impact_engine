import requests
from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.analyzer import calculate_risk
from core.explainer import explain_impact
from core.git_analyzer import get_changed_functions
from core.report_generator import generate_pr_report

BASE_DIR = "tests"  # adjust if needed


def handle_pr(payload, github_token):
    repo = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]

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

    post_comment(repo, pr_number, report, github_token)


def post_comment(repo, pr_number, report, token):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "body": f"```\\n{report}\\n```"
    }

    requests.post(url, headers=headers, json=data)