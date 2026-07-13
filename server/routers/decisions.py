from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import APIRouter, Query, Request

from server.schemas import DecisionResponse

router = APIRouter(prefix="/api/repos/{repo_id}", tags=["decisions"])


@router.get("/decisions", response_model=DecisionResponse)
async def get_decisions(
    repo_id: str,
    request: Request,
    status: str = Query("", description="Filter by status: active, deprecated, superseded"),
    limit: int = Query(50, description="Max decisions to return"),
) -> DecisionResponse:
    from core.decisions import extract_pr_decisions, mine_changelog_decisions, extract_adrs

    app_repo = request.app.state.repo_path
    repo_path = Path(app_repo or repo_id)

    all_decisions: list[dict] = []

    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-50"],
            capture_output=True, text=True, cwd=str(repo_path),
        )
        for line in result.stdout.strip().splitlines():
            for d in extract_pr_decisions(line):
                all_decisions.append({
                    "title": d.title,
                    "status": d.status,
                    "confidence": d.confidence,
                    "source": d.source,
                    "rationale": d.rationale,
                })
    except Exception:
        pass

    adr_dir = repo_path / "docs" / "adr"
    if adr_dir.is_dir():
        try:
            for d in extract_adrs(adr_dir):
                all_decisions.append({
                    "title": d.title,
                    "status": d.status,
                    "confidence": d.confidence,
                    "source": d.source,
                    "rationale": d.rationale,
                })
        except Exception:
            pass

    for name in ("CHANGELOG.md", "CHANGELOG.rst"):
        cl_path = repo_path / name
        if cl_path.exists():
            try:
                for d in mine_changelog_decisions(cl_path):
                    all_decisions.append({
                        "title": d.title,
                        "status": d.status,
                        "confidence": d.confidence,
                        "source": d.source,
                        "rationale": d.rationale,
                    })
            except Exception:
                pass

    if status:
        all_decisions = [d for d in all_decisions if d["status"] == status]

    return DecisionResponse(
        decisions=all_decisions[:limit],
        total=len(all_decisions),
    )
