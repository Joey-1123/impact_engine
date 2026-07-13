from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

from core.providers.base import BaseProvider, GeneratedResponse, ProviderError


class GeminiProvider(BaseProvider):
    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._client = genai.Client(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "gemini"

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
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
            usage = response.usage_metadata
            return GeneratedResponse(
                content=response.text or "",
                input_tokens=usage.prompt_token_count or 0 if usage else 0,
                output_tokens=usage.candidates_token_count or 0 if usage else 0,
            )
        except Exception as e:
            raise ProviderError("gemini", str(e)) from e
