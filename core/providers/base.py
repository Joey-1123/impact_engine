from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class GeneratedResponse:
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0


class ProviderError(Exception):
    def __init__(self, provider: str, message: str, status_code: int = 500) -> None:
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] {message}")


class RateLimitError(ProviderError):
    def __init__(self, provider: str, message: str = "Rate limited", retry_after: float = 30.0) -> None:
        self.retry_after = retry_after
        super().__init__(provider, message, status_code=429)


class BaseProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        request_id: str | None = None,
    ) -> GeneratedResponse: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...


class ChatProvider(Protocol):
    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        tools: list[Any] | None = None,
        system_prompt: str | None = None,
    ) -> Any: ...


class Embedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
