from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from core.health.models import Severity


@dataclass
class FileContext:
    file_path: str
    language: str
    nloc: int
    has_test_file: bool = False
    module: str | None = None
    function_metrics: dict[str, Any] = field(default_factory=dict)
    class_metrics: list[Any] = field(default_factory=list)
    git_meta: dict[str, Any] = field(default_factory=dict)
    dependents_count: int = 0
    pagerank_score: float = 0.0
    clones: list[Any] = field(default_factory=list)
    duplication_pct: float | None = None


@dataclass
class BiomarkerResult:
    biomarker_type: str
    severity: Severity
    function_name: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    details: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    deduction: float | None = None


class Biomarker(Protocol):
    name: str
    category: str
    def detect(self, ctx: FileContext) -> list[BiomarkerResult]: ...
