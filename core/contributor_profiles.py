from __future__ import annotations

from collections import Counter
from typing import Any


def count_active_contributors(
    git_meta_map: dict[str, dict[str, Any]],
    time_window_days: int = 90,
) -> int:
    seen: set[str] = set()
    for _file_path, meta in git_meta_map.items():
        authors = meta.get("top_authors_json", [])
        if isinstance(authors, list):
            for author in authors:
                name = ""
                if isinstance(author, dict):
                    name = author.get("name", "")
                elif isinstance(author, str):
                    name = author
                if name and isinstance(name, str):
                    seen.add(name)
    return max(len(seen), 1)


def compute_ownership(
    git_meta_map: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    file_owners: dict[str, dict[str, Any]] = {}
    for file_path, meta in git_meta_map.items():
        authors = meta.get("top_authors_json", [])
        if not isinstance(authors, list) or not authors:
            continue
        counts: Counter[str] = Counter()
        for author in authors:
            if isinstance(author, dict):
                counts[author.get("name", "")] += author.get("commit_count", 1)
            elif isinstance(author, str):
                counts[author] += 1
        if not counts:
            continue
        total = sum(counts.values())
        top_name, top_count = counts.most_common(1)[0]
        file_owners[file_path] = {
            "primary_owner": top_name,
            "ownership_share": round(top_count / total, 3) if total else 0,
            "total_contributors": len(counts),
        }
    return file_owners


def compute_bus_factor(
    file_owners: dict[str, dict[str, Any]],
    threshold: float = 0.8,
) -> dict[str, int]:
    bus_factor: dict[str, int] = {}
    for fpath, info in file_owners.items():
        share = info.get("ownership_share", 0)
        if share >= threshold:
            bus_factor[fpath] = 1
        else:
            bus_factor[fpath] = max(1, info.get("total_contributors", 1))
    return bus_factor
