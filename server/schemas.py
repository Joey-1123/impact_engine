from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HealthResponse:
    status: str = "healthy"
    version: str = ""


@dataclass
class OverviewResponse:
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    languages: dict[str, int] = field(default_factory=dict)
    layers: dict[str, int] = field(default_factory=dict)
    health_score: float = 0.0


@dataclass
class GraphResponse:
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    layers: list[str] = field(default_factory=list)
    fingerprint: str = ""


@dataclass
class HealthScoreResponse:
    overall: float = 0.0
    defect: float = 0.0
    maintainability: float = 0.0
    performance: float = 0.0
    findings_count: int = 0
    kpis: dict[str, float] = field(default_factory=dict)


@dataclass
class CostResponse:
    model: str = ""
    estimated_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    breakdown: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DecisionResponse:
    decisions: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0


@dataclass
class WorkspaceResponse:
    repos: list[dict[str, Any]] = field(default_factory=list)
    workspace_root: str = ""
    violation_count: int = 0
