from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProgressCallback(Protocol):
    def on_phase_start(self, phase: str, total: int | None = None) -> None: ...

    def on_item_done(self, phase: str) -> None: ...

    def on_phase_done(self, phase: str) -> None: ...

    def on_message(self, level: str, text: str) -> None: ...
