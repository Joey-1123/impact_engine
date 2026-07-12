from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HealthFindingData:
    biomarker_type: str
    severity: Severity
    file_path: str
    function_name: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    details: dict[str, Any] = field(default_factory=dict)
    health_impact: float = 0.0
    reason: str = ""
    dimension: str = "defect"


@dataclass
class HealthFileMetricData:
    file_path: str
    score: float
    max_ccn: int
    max_nesting: int
    nloc: int
    has_test_file: bool = False
    module: str | None = None
    duplication_pct: float | None = None
    line_coverage_pct: float | None = None
    defect_score: float | None = None
    maintainability_score: float | None = None
    performance_score: float | None = None


@dataclass
class HealthReport:
    repo_id: str
    analyzed_at: datetime
    findings: list[HealthFindingData] = field(default_factory=list)
    metrics: list[HealthFileMetricData] = field(default_factory=list)
    kpis: dict[str, Any] = field(default_factory=dict)
    refactoring_suggestions: list[Any] = field(default_factory=list)
