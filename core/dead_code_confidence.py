from __future__ import annotations

import re
from pathlib import PurePosixPath

SAFE_CONFIDENCE_THRESHOLD: float = 0.7
RISK_CAP_CONFIDENCE: float = 0.4

_FILENAME_RISK_TOKENS: dict[str, str] = {
    "config": "config", "configs": "config", "configuration": "config",
    "conf": "config", "settings": "config", "setting": "config", "setup": "config",
    "env": "environment", "environment": "environment", "environ": "environment",
    "dotenv": "environment",
    "bootstrap": "bootstrap", "startup": "bootstrap", "entrypoint": "bootstrap",
    "database": "database", "db": "database", "schema": "database",
    "seed": "database", "seeds": "database", "migration": "database",
    "migrations": "database", "datastore": "database", "sqlite": "database",
}

_DIRECTORY_RISK_TOKENS: dict[str, str] = {
    "config": "config", "configs": "config", "settings": "config",
    "env": "environment", "environments": "environment",
    "bootstrap": "bootstrap",
    "database": "database", "db": "database", "migrations": "database",
    "scripts": "script", "bin": "script", "tasks": "script",
}

_FACTOR_BLURB: dict[str, str] = {
    "config": "configuration",
    "environment": "environment/bootstrap",
    "bootstrap": "bootstrap/entry-point",
    "database": "database/schema",
    "script": "script/task",
}

_SPLIT_RE = re.compile(r"[._\-]+")


def path_risk_factors(file_path: str) -> tuple[str, ...]:
    if not file_path:
        return ()
    norm = file_path.replace("\\", "/")
    p = PurePosixPath(norm)
    factors: set[str] = set()
    for token in _SPLIT_RE.split(p.name.lower()):
        tag = _FILENAME_RISK_TOKENS.get(token)
        if tag:
            factors.add(tag)
    for segment in p.parent.parts:
        tag = _DIRECTORY_RISK_TOKENS.get(segment.lower())
        if tag:
            factors.add(tag)
    return tuple(sorted(factors))


def risk_evidence(factors: tuple[str, ...] | list[str]) -> str | None:
    if not factors:
        return None
    blurbs = ", ".join(_FACTOR_BLURB.get(f, f) for f in factors)
    return (
        f"Runtime-load risk ({blurbs}): files of this kind are often referenced "
        "outside static imports — review before deleting"
    )


def effective_safe_to_delete(
    confidence: float,
    file_path: str,
    stored_safe: bool = True,
) -> bool:
    if not stored_safe:
        return False
    if confidence < SAFE_CONFIDENCE_THRESHOLD:
        return False
    return not path_risk_factors(file_path)
