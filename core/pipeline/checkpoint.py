from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

CHECKPOINT_FILE = ".impact_pipeline_checkpoint"

PHASE_ORDER = ["ingestion", "analysis", "generation"]


@dataclass
class PipelineCheckpoint:
    completed_phases: set[str] = field(default_factory=set)
    running_phase: Optional[str] = None
    started_at: float = 0.0
    fingerprint: Optional[str] = None

    def is_completed(self, phase: str) -> bool:
        return phase in self.completed_phases

    def can_skip(self, phase: str) -> bool:
        idx = PHASE_ORDER.index(phase) if phase in PHASE_ORDER else -1
        if idx < 0:
            return False
        return all(
            PHASE_ORDER[i] in self.completed_phases for i in range(idx + 1)
        )

    @classmethod
    def load(cls, repo_path: Path) -> Optional[PipelineCheckpoint]:
        path = repo_path / CHECKPOINT_FILE
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(
                completed_phases=set(data.get("completed_phases", [])),
                running_phase=data.get("running_phase"),
                started_at=data.get("started_at", 0.0),
                fingerprint=data.get("fingerprint"),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def save(self, repo_path: Path) -> None:
        path = repo_path / CHECKPOINT_FILE
        data = {
            "completed_phases": list(self.completed_phases),
            "running_phase": self.running_phase,
            "started_at": self.started_at,
            "fingerprint": self.fingerprint,
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(path)

    def clear(self, repo_path: Path) -> None:
        path = repo_path / CHECKPOINT_FILE
        if path.exists():
            os.remove(path)


def compute_fingerprint(repo_path: Path) -> str:
    tracker: dict[str, float] = {}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {
            ".venv", "venv", "env", "__pycache__", "node_modules", "build", "dist"
        }]
        for f in files:
            if f.endswith(".py"):
                fp = os.path.join(root, f)
                try:
                    tracker[fp] = os.path.getmtime(fp)
                except OSError:
                    continue
    h = hashlib.sha256()
    for fp in sorted(tracker):
        h.update(fp.encode())
        h.update(str(tracker[fp]).encode())
    return h.hexdigest()
