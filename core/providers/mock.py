from __future__ import annotations

from core.providers.base import BaseProvider, GeneratedResponse


class MockProvider(BaseProvider):
    provider_name = "mock"
    model_name = "mock-model"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        request_id: str | None = None,
    ) -> GeneratedResponse:
        return GeneratedResponse(
            content=f"[mock response to: {user_prompt[:50]}]",
            input_tokens=len(system_prompt) + len(user_prompt),
            output_tokens=50,
        )


class MockEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        import hashlib
        results: list[list[float]] = []
        for text in texts:
            h = hashlib.sha256(text.encode()).digest()
            vec = [b / 255.0 for b in h[:16]]
            results.append(vec)
        return results
