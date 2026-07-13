from __future__ import annotations

from openai import AsyncOpenAI

from core.providers.base import ProviderError


class OpenAIEmbedder:
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=texts,
            )
            return [d.embedding for d in response.data]
        except Exception as e:
            raise ProviderError("openai_embedder", str(e)) from e
