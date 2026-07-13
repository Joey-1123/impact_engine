# ADR 001: Multi-language parser architecture

**Status:** Active
**Date:** 2026-07-13

## Context

Impact Engine needs to analyze codebases that contain multiple programming
languages. Rather than building a single monolithic parser, we need an
extensible plugin system.

## Decision

Use a registry-based parser plugin architecture where:

1. Each language implements `BaseParser` with `extract_dependencies()`
2. Parser classes are registered via `@register_parser(ext)` decorator
3. Auto-discovery via `pkgutil.iter_modules` finds all parsers
4. The registry maps file extensions to parser classes
5. `extract_project_dependencies()` queries `get_parser(file)` per file

## Consequences

- Adding a new language: create a parser file + register extension
- Python is the full-featured parser (AST, all 26 biomarkers)
- Go/Rust/Java use regex-based extraction (no tree-sitter dependency)
- The plugin system is decoupled from the extraction pipeline
