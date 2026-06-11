# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from pathlib import Path
import os


def get_project_root() -> str:
    configured = os.getenv("IMPACT_ENGINE_PROJECT_ROOT")
    if configured:
        return str(Path(configured).expanduser().resolve())

    return str(Path(__file__).resolve().parents[1])
