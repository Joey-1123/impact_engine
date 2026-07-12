from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.git_analyzer import run_git

_MAX_BLAME_SIZE_BYTES = 5 * 1024 * 1024
_MIN_COMMITS_FOR_BLAME = 5


@dataclass
class BlameIndex:
    lines: dict[int, tuple[str, int]] = field(default_factory=dict)
    authors: dict[str, tuple[str, str]] = field(default_factory=dict)


def _parse_porcelain(
    raw: str,
) -> tuple[dict[int, tuple[str, int]], dict[str, tuple[str, str]]]:
    out: dict[int, tuple[str, int]] = {}
    authors: dict[str, tuple[str, str]] = {}
    current_sha: str | None = None
    current_final: int | None = None
    current_author_time: int = 0
    current_author_name: str | None = None
    current_author_email: str | None = None
    sha_author_time: dict[str, int] = {}

    for line in raw.splitlines():
        if not line:
            continue
        if line.startswith("\t"):
            if current_sha is not None and current_final is not None:
                t = current_author_time or sha_author_time.get(current_sha, 0)
                out[current_final] = (current_sha, t)
                if current_sha not in authors and current_author_name:
                    authors[current_sha] = (
                        current_author_name,
                        (current_author_email or "").strip("<>"),
                    )
            current_sha = None
            current_final = None
            current_author_time = 0
            current_author_name = None
            current_author_email = None
            continue
        if line.startswith("author-time "):
            try:
                current_author_time = int(line.split(" ", 1)[1])
            except (ValueError, IndexError):
                current_author_time = 0
            if current_sha is not None and current_author_time:
                sha_author_time[current_sha] = current_author_time
            continue
        if line.startswith("author "):
            current_author_name = line[len("author "):].strip() or "unknown"
            continue
        if line.startswith("author-mail "):
            current_author_email = line[len("author-mail "):].strip()
            continue
        head, _, rest = line.partition(" ")
        if len(head) == 40 and all(c in "0123456789abcdef" for c in head):
            parts = line.split(" ")
            current_sha = parts[0]
            if len(parts) >= 3:
                try:
                    current_final = int(parts[2])
                except ValueError:
                    current_final = None
            current_author_time = sha_author_time.get(current_sha, 0)
    return out, authors


def build_blame_index(
    file_path: str,
    cwd: str | None = None,
    *,
    commit_count_total: int = 0,
) -> BlameIndex:
    if commit_count_total and commit_count_total < _MIN_COMMITS_FOR_BLAME:
        return BlameIndex()
    if cwd:
        try:
            full = Path(cwd) / file_path
            if full.stat().st_size > _MAX_BLAME_SIZE_BYTES:
                return BlameIndex()
        except OSError:
            return BlameIndex()
    result = run_git(
        ["blame", "--line-porcelain", "HEAD", "--", file_path],
        cwd=cwd,
    )
    if result.returncode != 0 or not result.stdout:
        return BlameIndex()
    lines, authors = _parse_porcelain(result.stdout)
    return BlameIndex(lines=lines, authors=authors)


def distinct_commits_in_range(idx: BlameIndex, start_line: int, end_line: int) -> set[str]:
    if not idx.lines or start_line > end_line:
        return set()
    out: set[str] = set()
    for ln in range(start_line, end_line + 1):
        entry = idx.lines.get(ln)
        if entry is not None:
            out.add(entry[0])
    return out


def median_author_time_in_range(idx: BlameIndex, start_line: int, end_line: int) -> int | None:
    if not idx.lines or start_line > end_line:
        return None
    times = [
        idx.lines[ln][1]
        for ln in range(start_line, end_line + 1)
        if ln in idx.lines and idx.lines[ln][1] > 0
    ]
    if not times:
        return None
    times.sort()
    n = len(times)
    mid = n // 2
    if n % 2:
        return times[mid]
    return (times[mid - 1] + times[mid]) // 2


def recent_commits_in_range(
    idx: BlameIndex,
    start_line: int,
    end_line: int,
    *,
    since_unix_ts: int,
) -> set[str]:
    if not idx.lines or start_line > end_line:
        return set()
    out: set[str] = set()
    for ln in range(start_line, end_line + 1):
        entry = idx.lines.get(ln)
        if entry is None:
            continue
        sha, ts = entry
        if ts >= since_unix_ts:
            out.add(sha)
    return out


def owner_in_range(
    idx: BlameIndex, start_line: int, end_line: int
) -> tuple[str | None, str | None, float | None]:
    if not idx.lines or start_line > end_line:
        return None, None, None
    counts: Counter[str] = Counter()
    for ln in range(start_line, end_line + 1):
        entry = idx.lines.get(ln)
        if entry is None:
            continue
        name = idx.authors.get(entry[0], ("unknown", ""))[0]
        counts[name] += 1
    if not counts:
        return None, None, None
    total = sum(counts.values())
    top_name, top_count = counts.most_common(1)[0]
    top_email = ""
    for sha, (name, email) in idx.authors.items():
        if name == top_name and email:
            top_email = email
            break
    return top_name, top_email or None, (top_count / total if total else None)


def ownership_from_blame(idx: BlameIndex) -> tuple[str | None, str | None, float | None]:
    if not idx.lines:
        return None, None, None
    counts: Counter[str] = Counter()
    for sha, _ts in idx.lines.values():
        name = idx.authors.get(sha, ("unknown", ""))[0]
        counts[name] += 1
    if not counts:
        return None, None, None
    total = sum(counts.values())
    top_name, top_count = counts.most_common(1)[0]
    top_email = ""
    for sha, (name, email) in idx.authors.items():
        if name == top_name and email:
            top_email = email
            break
    return top_name, top_email, top_count / total if total else None
