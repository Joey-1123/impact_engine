from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_TOKEN_PATTERN = re.compile(r"[a-zA-Z_]\w*|[^\s]")
_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_]\w*$")
_BASE = 131
_MOD = 2**61 - 1


def normalize_token(t: str) -> str:
    if _IDENTIFIER_RE.match(t):
        return "$id"
    if t.startswith(('"', "'")) or t.startswith(("f'", 'f"', "b'", 'b"')):
        return "$str"
    return t


def tokenize(source: str) -> list[str]:
    tokens: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "/*", "*", "//")):
            continue
        for m in _TOKEN_PATTERN.finditer(stripped):
            tokens.append(normalize_token(m.group()))
    return tokens


def rolling_hash(tokens: list[str], window: int = 50) -> dict[int, list[int]]:
    if len(tokens) < window:
        return {}
    power = pow(_BASE, window - 1, _MOD)
    h = 0
    for i in range(window):
        h = (h * _BASE + hash(tokens[i])) % _MOD
    buckets: dict[int, list[int]] = {h: [0]}
    for i in range(window, len(tokens)):
        h = (h - hash(tokens[i - window]) * power) % _MOD
        h = (h * _BASE + hash(tokens[i])) % _MOD
        buckets.setdefault(h, []).append(i - window + 1)
    return {k: v for k, v in buckets.items() if len(v) > 1}


@dataclass
class ClonePair:
    file_a: str
    start_a: int
    file_b: str
    start_b: int
    length: int
    similarity: float = 0.0


@dataclass
class DuplicationReport:
    pairs: list[ClonePair] = field(default_factory=list)
    total_clones: int = 0
    duplicated_lines: int = 0


def find_clones(
    files: dict[str, str],
    window: int = 50,
    min_length: int = 20,
) -> DuplicationReport:
    file_tokens: dict[str, list[str]] = {}
    file_hash_buckets: dict[str, dict[int, list[int]]] = {}

    for fpath, source in files.items():
        tokens = tokenize(source)
        if len(tokens) < window:
            continue
        file_tokens[fpath] = tokens
        file_hash_buckets[fpath] = rolling_hash(tokens, window=window)

    seen_pairs: set[tuple[str, int, str, int]] = set()
    pairs: list[ClonePair] = []

    paths = list(file_hash_buckets.keys())
    for i in range(len(paths)):
        for j in range(i, len(paths)):
            fa = paths[i]
            fb = paths[j]
            buckets_a = file_hash_buckets[fa]
            buckets_b = file_hash_buckets[fb]

            for h, starts_a in buckets_a.items():
                starts_b = buckets_b.get(h)
                if starts_b is None:
                    continue
                for sa in starts_a:
                    for sb in starts_b:
                        if fa == fb and abs(sa - sb) < window:
                            continue
                        key = (fa, sa, fb, sb)
                        if key in seen_pairs:
                            continue
                        seen_pairs.add(key)
                        if key[::-1] in seen_pairs:
                            continue

                        length = _measure_overlap(
                            file_tokens[fa], sa,
                            file_tokens[fb], sb,
                            window,
                        )
                        if length < min_length:
                            continue
                        tokens_a = file_tokens[fa][sa:sa + length]
                        tokens_b = file_tokens[fb][sb:sb + length]
                        matches = sum(1 for x, y in zip(tokens_a, tokens_b, strict=True) if x == y)
                        similarity = matches / length if length else 0

                        pairs.append(ClonePair(
                            file_a=fa, start_a=sa,
                            file_b=fb, start_b=sb,
                            length=length,
                            similarity=similarity,
                        ))

    pairs.sort(key=lambda p: -p.length * p.similarity)
    duplicated_lines = sum(p.length for p in pairs)

    return DuplicationReport(
        pairs=pairs[:500],
        total_clones=len(pairs),
        duplicated_lines=duplicated_lines,
    )


def _measure_overlap(
    tokens_a: list[str], sa: int,
    tokens_b: list[str], sb: int,
    min_overlap: int,
) -> int:
    length = min_overlap
    while (sa + length < len(tokens_a) and
           sb + length < len(tokens_b) and
           tokens_a[sa + length] == tokens_b[sb + length]):
        length += 1
    return length
