from __future__ import annotations

from typing import Any, Callable

_PROVIDER_FACTORIES: dict[str, Callable[..., Any]] = {}
_EMBEDDER_FACTORIES: dict[str, Callable[..., Any]] = {}


def register_provider(name: str, factory: Callable[..., Any]) -> None:
    _PROVIDER_FACTORIES[name] = factory


def get_provider(name: str, **kwargs: Any) -> Any:
    factory = _PROVIDER_FACTORIES.get(name)
    if factory is None:
        raise ValueError(f"Unknown provider: {name}. Available: {list_providers()}")
    return factory(**kwargs)


def list_providers() -> list[str]:
    return list(_PROVIDER_FACTORIES.keys())


def register_embedder(name: str, factory: Callable[..., Any]) -> None:
    _EMBEDDER_FACTORIES[name] = factory


def get_embedder(name: str, **kwargs: Any) -> Any:
    factory = _EMBEDDER_FACTORIES.get(name)
    if factory is None:
        raise ValueError(f"Unknown embedder: {name}. Available: {list_embedders()}")
    return factory(**kwargs)


def list_embedders() -> list[str]:
    return list(_EMBEDDER_FACTORIES.keys())
