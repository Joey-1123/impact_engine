# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import os
import json
from typing import Any, Dict, List, Optional

CONFIG_FILES = [".impactrc", ".impactrc.json", "impact-engine.json", "impact-engine.toml"]


def _find_config(path: str) -> Optional[str]:
    if os.path.isfile(path) and os.path.basename(path) in CONFIG_FILES:
        return path
    if os.path.isdir(path):
        for name in CONFIG_FILES:
            candidate = os.path.join(path, name)
            if os.path.isfile(candidate):
                return candidate
    return None


def _parse_toml(file_path: str) -> dict:
    try:
        import tomllib
        with open(file_path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        try:
            import tomli
            with open(file_path, "rb") as f:
                return tomli.load(f)
        except ImportError:
            pass
    return {}


def _parse_json(file_path: str) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_config(path: str) -> Dict[str, Any]:
    config_path = _find_config(path)
    if not config_path:
        return {}

    ext = os.path.splitext(config_path)[1]
    if ext == ".toml":
        raw = _parse_toml(config_path)
    else:
        raw = _parse_json(config_path)

    section = raw.get("impact-engine", raw)

    return {
        "ignore_dirs": set(section.get("ignore_dirs", [])),
        "entry_points": section.get("entry_points", []),
        "max_depth": section.get("max_depth", 3),
        "max_children": section.get("max_children", 12),
        "max_nodes": section.get("max_nodes", 200),
        "risk_threshold_high": section.get("risk_threshold_high", 5),
        "risk_threshold_medium": section.get("risk_threshold_medium", 3),
        "json_output": section.get("json", False),
        "limit": section.get("limit", 10),
        "use_cache": section.get("use_cache", True),
        "respect_gitignore": section.get("respect_gitignore", True),
    }


def merge_config(args: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(config)
    for key, val in args.items():
        if val is not None:
            merged[key] = val
    return merged
