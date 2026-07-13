from __future__ import annotations

from typing import Any

from core.persistence.vector_store.base import VectorStore, SearchResult, cosine_similarity, Embedder


class InMemoryVectorStore(VectorStore):
    def __init__(self, embedder: Embedder | None = None) -> None:
        self._embedder = embedder
        self._data: dict[str, tuple[list[float], dict[str, Any]]] = {}

    async def _get_embedder(self) -> Embedder:
        if self._embedder is not None:
            return self._embedder
        from core.providers.mock import MockEmbedder
        return MockEmbedder()

    async def embed_and_upsert(
        self, page_id: str, text: str, metadata: dict[str, Any] | None = None
    ) -> None:
        embedder = await self._get_embedder()
        vectors = await embedder.embed([text])
        self._data[page_id] = (vectors[0], metadata or {})

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        embedder = await self._get_embedder()
        qvec = (await embedder.embed([query]))[0]
        scored: list[tuple[float, str, dict[str, Any]]] = []
        for pid, (vec, meta) in self._data.items():
            sim = cosine_similarity(qvec, vec)
            scored.append((sim, pid, meta))
        scored.sort(key=lambda x: -x[0])
        results: list[SearchResult] = []
        for sim, pid, meta in scored[:limit]:
            results.append(
                SearchResult(
                    page_id=pid,
                    title=meta.get("title", ""),
                    page_type=meta.get("page_type", ""),
                    target_path=meta.get("target_path", ""),
                    score=sim,
                    snippet=meta.get("snippet", ""),
                )
            )
        return results

    async def delete(self, page_id: str) -> None:
        self._data.pop(page_id, None)

    async def close(self) -> None:
        self._data.clear()
