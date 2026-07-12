from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (0.003, 0.015),
    "claude-haiku-4-5": (0.001, 0.005),
    "claude-opus-4-6": (0.005, 0.025),
    "gpt-5.4": (0.0025, 0.015),
    "gpt-5.4-mini": (0.00075, 0.0045),
    "gemini-3.1-pro": (0.002, 0.012),
    "gemini-3-flash": (0.0005, 0.003),
}

_HEURISTIC_TOKENS: dict[str, tuple[int, int]] = {
    "file_summary": (400, 100),
    "layer_naming": (600, 50),
    "tour_step": (300, 80),
    "decision_title": (200, 30),
    "refactoring_plan": (800, 200),
}


@dataclass
class CostEstimate:
    model: str
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    breakdown: list[dict[str, Any]] = field(default_factory=list)


def estimate_cost(
    page_types: list[str],
    count: int = 1,
    model: str = "claude-sonnet-4-6",
) -> CostEstimate:
    pricing = _PRICING.get(model, (0.003, 0.015))
    input_rate, output_rate = pricing

    total_input = 0
    total_output = 0
    breakdown: list[dict[str, Any]] = []

    for pt in page_types:
        in_tok, out_tok = _HEURISTIC_TOKENS.get(pt, (500, 100))
        total_input += in_tok * count
        total_output += out_tok * count
        breakdown.append({
            "page_type": pt,
            "count": count,
            "input_tokens": in_tok * count,
            "output_tokens": out_tok * count,
        })

    cost = (total_input / 1000) * input_rate + (total_output / 1000) * output_rate

    return CostEstimate(
        model=model,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        estimated_cost_usd=round(cost, 4),
        breakdown=breakdown,
    )
