from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from core.providers.base import BaseProvider, GeneratedResponse, ProviderError


class OpenAIProvider(BaseProvider):
    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @property
    def provider_name(self) -> str:
        return "openai"

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
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            choice = response.choices[0]
            usage = response.usage
            return GeneratedResponse(
                content=choice.message.content or "",
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )
        except Exception as e:
            raise ProviderError("openai", str(e)) from e
