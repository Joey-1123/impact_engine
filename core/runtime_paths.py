from pathlib import Path
import os


def get_project_root():
    """
    Resolve the repository root for the current checkout.

    Allows an override via IMPACT_ENGINE_PROJECT_ROOT for deployments or
    multi-repo environments, otherwise falls back to the repo root adjacent
    to this package.
    """
    configured = os.getenv("IMPACT_ENGINE_PROJECT_ROOT")
    if configured:
        return str(Path(configured).expanduser().resolve())

    return str(Path(__file__).resolve().parents[1])
