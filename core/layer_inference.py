from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath

_TEST_DIR_TOKENS = frozenset({"__tests__", "test", "tests", "spec", "specs", "e2e"})

_LAYER_HINTS: tuple[tuple[str, frozenset[str]], ...] = (
    ("CLI", frozenset({"cli", "commands", "cmd", "cli_commands"})),
    ("API", frozenset({"routes", "api", "controllers", "endpoints", "handlers", "routers"})),
    ("Service", frozenset({"services", "core", "lib", "domain", "logic", "usecases"})),
    ("Data", frozenset({"models", "db", "data", "persistence", "repository", "repositories", "store", "stores", "entities"})),
    ("UI", frozenset({"components", "views", "pages", "ui", "layouts", "widgets", "screens"})),
    ("Middleware", frozenset({"middleware", "plugins", "interceptors", "guards"})),
    ("Utility", frozenset({"utils", "helpers", "common", "shared", "tools", "util"})),
    ("Config", frozenset({"config", "constants", "env", "settings", "conf"})),
    ("Test", _TEST_DIR_TOKENS),
    ("Types", frozenset({"types", "interfaces", "schemas", "contracts", "dtos", "typings"})),
)

ADJACENT_LAYERS: frozenset[str] = frozenset({"Test"})

_AMBIGUOUS_TEST_DIR_TOKENS: frozenset[str] = frozenset({"spec", "specs"})

_EXAMPLE_DIR_TOKENS = frozenset({
    "examples", "_examples", "example", "samples", "sample", "demo", "demos",
    "bench", "benches", "benchmarks",
})

_DOC_DIR_TOKENS = frozenset({"docs", "doc", "website"})

_TOOLING_DIR_TOKENS = frozenset({"scripts", "script", "docker", "plugins"})

DOCS_TOOLING_LAYER = "Docs & Tooling"

_NON_ARCH_DIR_TOKENS = _EXAMPLE_DIR_TOKENS | _DOC_DIR_TOKENS | _TOOLING_DIR_TOKENS

DEFAULT_LAYER = "Application"

_CANONICAL_RANK: dict[str, int] = {
    "UI": 0, "CLI": 1, "API": 2, "Middleware": 3, "Service": 4,
    DEFAULT_LAYER: 5, "Data": 6, "Types": 7, "Config": 8, "Utility": 9,
    DOCS_TOOLING_LAYER: 10, "Test": 11,
}

_PINNED_AFTER_RUNTIME: frozenset[str] = ADJACENT_LAYERS | {DOCS_TOOLING_LAYER}


def infer_layer(path: str, language: str | None = None) -> str:
    original_parts = list(PurePosixPath(path).parts)
    parts = [s.lower() for s in original_parts]
    filename = original_parts[-1] if original_parts else ""
    segments = parts[:-1]

    stem = PurePosixPath(filename).stem.lower()
    if stem.startswith(("test_", "spec_")) or stem.endswith(("_test", "_spec", "_specs")):
        return "Test"

    for seg in segments:
        if seg not in _TEST_DIR_TOKENS:
            continue
        if seg in _AMBIGUOUS_TEST_DIR_TOKENS:
            continue
        return "Test"

    if segments and segments[0].startswith("."):
        return "Config"

    if any(seg in _NON_ARCH_DIR_TOKENS for seg in segments):
        return DOCS_TOOLING_LAYER

    for i in range(len(segments) - 1, -1, -1):
        seg = segments[i]
        for layer_name, tokens in _LAYER_HINTS:
            if layer_name == "Test":
                continue
            if seg in tokens:
                return layer_name

    return DEFAULT_LAYER


def compute_layer_order(
    file_layers: Mapping[str, str],
    import_edges: Iterable[tuple[str, str]] | None = None,
) -> list[str]:
    layers = sorted(set(file_layers.values()))
    if len(layers) <= 1:
        return layers

    runtime = [layer for layer in layers if layer not in _PINNED_AFTER_RUNTIME]
    adjacent = [layer for layer in layers if layer in _PINNED_AFTER_RUNTIME]

    out_deg: dict[str, int] = defaultdict(int)
    in_deg: dict[str, int] = defaultdict(int)

    if import_edges:
        for src, dst in import_edges:
            ls = file_layers.get(src)
            ld = file_layers.get(dst)
            if not ls or not ld or ls == ld:
                continue
            if ls in _PINNED_AFTER_RUNTIME or ld in _PINNED_AFTER_RUNTIME:
                continue
            out_deg[ls] += 1
            in_deg[ld] += 1

    def sort_key(layer: str) -> tuple[int, int]:
        net = in_deg[layer] - out_deg[layer]
        return (net, _CANONICAL_RANK.get(layer, len(_CANONICAL_RANK)))

    ordered = sorted(runtime, key=sort_key)
    ordered += sorted(adjacent, key=lambda la: _CANONICAL_RANK.get(la, len(_CANONICAL_RANK)))
    return ordered
