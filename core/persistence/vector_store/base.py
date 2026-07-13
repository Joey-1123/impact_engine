from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class SearchResult:
    page_id: str
    title: str = ""
    page_type: str = ""
    target_path: str = ""
    score: float = 0.0
    snippet: str = ""


class Embedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class VectorStore(ABC):
    @abstractmethod
    async def embed_and_upsert(
        self, page_id: str, text: str, metadata: dict[str, Any] | None = None
    ) -> None: ...

    @abstractmethod
    async def search(
        self, query: str, limit: int = 10
    ) -> list[SearchResult]: ...

    @abstractmethod
    async def delete(self, page_id: str) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...
