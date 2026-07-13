from __future__ import annotations

from pathlib import Path
from typing import Any

import lancedb

from core.persistence.vector_store.base import VectorStore, SearchResult, cosine_similarity, Embedder


class LanceDBVectorStore(VectorStore):
    def __init__(
        self,
        uri: str = "./.impact_engine/vectors",
        table_name: str = "vectors",
        embedder: Embedder | None = None,
    ) -> None:
        self._uri = uri
        self._table_name = table_name
        self._embedder = embedder
        self._db = lancedb.connect(uri)
        self._table = None
        self._init_table()

    def _init_table(self) -> None:
        try:
            self._table = self._db.open_table(self._table_name)
        except Exception:
            import pyarrow as pa
            schema = pa.schema([
                pa.field("page_id", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), 1536)),
                pa.field("title", pa.string()),
                pa.field("page_type", pa.string()),
                pa.field("target_path", pa.string()),
                pa.field("snippet", pa.string()),
                pa.field("metadata_json", pa.string()),
            ])
            self._table = self._db.create_table(self._table_name, schema=schema)

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
        meta = metadata or {}
        import json
        import pyarrow as pa
        row = pa.table({
            "page_id": [page_id],
            "vector": [vectors[0]],
            "title": [meta.get("title", "")],
            "page_type": [meta.get("page_type", "")],
            "target_path": [meta.get("target_path", "")],
            "snippet": [meta.get("snippet", "")],
            "metadata_json": [json.dumps(meta)],
        })
        assert self._table is not None
        self._table.merge_insert("page_id").when_matched_update_all().execute(row)

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        embedder = await self._get_embedder()
        qvec = (await embedder.embed([query]))[0]
        assert self._table is not None
        results = (
            self._table.search(qvec).limit(limit).to_list()
        )
        return [
            SearchResult(
                page_id=r["page_id"],
                title=r.get("title", ""),
                page_type=r.get("page_type", ""),
                target_path=r.get("target_path", ""),
                score=r.get("_distance", 0.0),
                snippet=r.get("snippet", ""),
            )
            for r in results
        ]

    async def delete(self, page_id: str) -> None:
        assert self._table is not None
        self._table.delete(f"page_id = '{page_id}'")

    async def close(self) -> None:
        pass
