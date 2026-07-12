from __future__ import annotations

import contextlib

from ..progress import ProgressCallback


def phase_done(progress: ProgressCallback | None, phase: str) -> None:
    if progress is None:
        return
    fn = getattr(progress, "on_phase_done", None)
    if callable(fn):
        with contextlib.suppress(Exception):
            fn(phase)
