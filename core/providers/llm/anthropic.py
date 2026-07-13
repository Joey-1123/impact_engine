from __future__ import annotations

from typing import Any

from anthropic import AsyncAnthropic

from core.providers.base import BaseProvider, GeneratedResponse, ProviderError


class AnthropicProvider(BaseProvider):
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._client = AsyncAnthropic(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        request_id: str | None = None,
    ) -> GeneratedResponse:
        try:
            response = await self._client.messages.create(
                model=self._model,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = "".join(
                b.text for b in response.content if b.type == "text"
            )
            usage = response.usage
            return GeneratedResponse(
                content=content,
                input_tokens=usage.input_tokens if usage else 0,
                output_tokens=usage.output_tokens if usage else 0,
            )
        except Exception as e:
            raise ProviderError("anthropic", str(e)) from e
