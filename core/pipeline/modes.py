from __future__ import annotations

import enum

__all__ = ["OrchestratorMode"]


class OrchestratorMode(enum.StrEnum):
    STANDARD = "standard"
    FAST = "fast"
    ESSENTIAL = "essential"

    @property
    def allows_llm(self) -> bool:
        return self is OrchestratorMode.STANDARD

    @property
    def allows_full_git(self) -> bool:
        return self is not OrchestratorMode.ESSENTIAL
