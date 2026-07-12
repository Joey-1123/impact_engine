from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_DECISION_VERBS = re.compile(
    r"\b(use|chose|decided|migrate|adopt|replace|move|extract|split|rename|upgrade|downgrade|switch|introduce|remove|deprecate|add|implement|refactor|redesign|restructure)\b",
    re.IGNORECASE,
)

_CAUSAL_MARKERS = re.compile(
    r"\b(because|since|so that|in order to|to avoid|to fix|to support|reason|rationale|motivation|trade.?off|alternative)\b",
    re.IGNORECASE,
)


@dataclass
class ExtractedDecision:
    title: str
    decision: str
    rationale: str = ""
    affected_files: list[str] = field(default_factory=list)
    source: str = ""
    confidence: float = 0.5
    status: str = "active"


def mine_changelog_decisions(changelog_path: Path) -> list[ExtractedDecision]:
    if not changelog_path.exists():
        return []
    text = changelog_path.read_text(encoding="utf-8")
    decisions: list[ExtractedDecision] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if _DECISION_VERBS.search(line) and _CAUSAL_MARKERS.search(line):
            decisions.append(
                ExtractedDecision(
                    title=line[:80],
                    decision=line,
                    source=str(changelog_path),
                    confidence=0.4,
                )
            )
    return decisions


def extract_pr_decisions(pr_body: str, pr_number: int = 0) -> list[ExtractedDecision]:
    decisions: list[ExtractedDecision] = []
    for line in pr_body.splitlines():
        line = line.strip()
        if not line:
            continue
        if _DECISION_VERBS.search(line) and _CAUSAL_MARKERS.search(line):
            decisions.append(
                ExtractedDecision(
                    title=f"PR #{pr_number}: {line[:60]}",
                    decision=line,
                    source=f"PR #{pr_number}",
                    confidence=0.5,
                )
            )
    return decisions


def extract_adrs(adr_dir: Path) -> list[ExtractedDecision]:
    if not adr_dir.is_dir():
        return []
    decisions: list[ExtractedDecision] = []
    for f in sorted(adr_dir.iterdir()):
        if f.suffix.lower() in (".md", ".rst", ".txt"):
            text = f.read_text(encoding="utf-8")
            title_match = re.search(r"^#\s+(.+)", text, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else f.stem
            status_match = re.search(r"##\s+Status\s*\n\s*(.+)", text, re.MULTILINE | re.IGNORECASE)
            status = status_match.group(1).strip() if status_match else "active"
            decisions.append(
                ExtractedDecision(
                    title=title,
                    decision=title,
                    rationale=text[:500],
                    source=str(f),
                    confidence=0.8,
                    status=status,
                )
            )
    return decisions
