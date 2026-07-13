# Impact Engine

**Python-based static analysis framework — function-level dependency graphs, health scoring, knowledge graphs, and AI agent tooling.**

---

## Repository layout

| Path | Role |
|---|---|
| **`cli/`** | Argparse entry point (`main.py`) — 25+ commands, thin dispatch layer |
| **`core/`** | All analysis logic — graph building, health scoring, knowledge graph, extraction |
| **`core/health/`** | Scoring engine + 26 biomarker detectors (structural, performance, organizational) |
| **`core/graph/`** | Knowledge graph construction, PageRank, community detection, layer inference |
| **`core/parsers/`** | Language-specific parsers (Python, JS/TS, Go, Rust, Java) |
| **`core/providers/`** | LLM providers (OpenAI, Anthropic, Gemini) + embedding providers |
| **`core/persistence/`** | Vector store (InMemory, LanceDB) |
| **`core/pipeline/`** | Orchestrator with phased execution (ingestion → analysis → generation) |
| **`server/`** | FastAPI REST API + MCP server for AI agents |
| **`impact_web/`** | Django web dashboard |
| **`web/`** | Next.js 15 frontend dashboard |
| **`tests/`** | Unit tests (unittest + pytest) |

Commands assume **repo root**.

---

## Runtime scope

- **CLI tool**: `impact-engine -p /path/to/project <command>` — primary interface.
- **REST API**: `impact-engine -p /path/to/project serve --port 8000` — FastAPI with 7 endpoint groups.
- **MCP server**: `impact-engine -p /path/to/project mcp --port 8001` — 9 tools for AI coding agents.
- **Web dashboard**: Next.js app at `web/` — graph explorer, health view, decision viewer.

**Where logic lives:**

- **`core/`**: all analysis, scoring, graph construction, extraction. Authoritative.
- **`cli/`**: thin command dispatch. No business logic.
- **`server/`**: HTTP/MCP transport. Delegates to `core/`.

---

## Commands (from repo root)

```bash
# Install
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install rich fastapi uvicorn mcp lancedb openai anthropic google-genai

# Analysis
impact-engine -p /path/to/project analyze        # Full analysis pipeline
impact-engine -p /path/to/project health --json   # Health scoring (26 biomarkers)
impact-engine -p /path/to/project kg --json       # Knowledge graph
impact-engine -p /path/to/project duplication     # Clone detection
impact-engine -p /path/to/project decisions       # Decision mining
impact-engine -p /path/to/project cycles          # Circular dependency detection
impact-engine -p /path/to/project complexity      # Cyclomatic complexity

# Servers
impact-engine -p /path/to/project serve --port 8000   # REST API
impact-engine -p /path/to/project mcp --port 8001     # MCP server

# Development
make test          # Run unit tests
make build         # Build package
make clean         # Clean build artifacts
```

---

## Testing

### Unit tests

```bash
# Using unittest
python -m unittest discover -s tests -p "test_*.py" -v

# Using pytest
pytest tests/ -v

# Single test file
pytest tests/test_core.py -v
```

- Co-locate as `test_*.py` under `tests/`.
- Prefer behavior over implementation. No real network, no time flakes.
- All 34 tests must pass before merging.

### What to test

- Extractor: import resolution, stdlib detection, relative imports
- Graph builder: cycle detection, entry points, dead code detection
- Health scoring: each biomarker detector, scoring dimensions
- Knowledge graph: PageRank, community detection, layer inference
- CLI commands: argument parsing, JSON output, error handling

---

## Architecture

```
Parse → Graph → Analyze → Enrich → Serve

AST        nx.DiGraph   Dead Code    Knowledge   CLI
Extraction               Cycles       Graph       FastAPI
+ Line #s   call/import  Entry Points  PageRank    Next.js
+ CCN       edges        Health       Communities MCP
```

The pipeline runs in under 30 seconds on a 3,000-file repository and caches results for incremental updates.

### Health scoring

26 biomarkers across three dimensions:

| Dimension | Biomarkers |
|---|---|
| **Defect risk** | brain method, god class, complex method, large method, nested complexity, primitive obsession, complex conditional, low cohesion, bumpy road, large class, DRY violation, error handling |
| **Maintainability** | code clarity, duplication, class size, ownership concentration, bus factor |
| **Performance** | IO-in-loop, string-concat-in-loop, blocking-sync-in-async |

### Knowledge graph

- **PageRank** — identifies architecturally significant nodes
- **Community detection** — greedy modularity optimization
- **Layer classification** — Application, Domain, Persistence, Presentation, Test, Config, Utility
- **Entry-point tours** — ranked walkthrough from `main()` and other entry points

---

## Project conventions

### Code style

- **No comments** unless explicitly asked.
- Keep functions focused and under ~200 lines.
- Use `pathlib.Path` over `os.path`.
- Use type hints on public functions.
- Follow existing patterns in neighboring files.

### Module shape

| File | Role |
|---|---|
| `__init__.py` | Public API exports |
| `models.py` / `_models.py` | Dataclasses, Pydantic models, typed dicts |
| `_base.py` | Shared utilities, base classes |
| `*_detectors.py` | Biomarker detection functions |
| `scoring.py` | Score computation logic |

### Adding a new biomarker

1. Create detector function in appropriate `core/health/biomarkers/` file.
2. Register in `core/health/biomarkers/__init__.py`.
3. Add scoring logic in `core/health/scoring.py`.
4. Add tests in `tests/`.
5. Update README.md biomarker list.

### Adding a new CLI command

1. Add command function in `cli/main.py`.
2. Register argparse subcommand.
3. Add `--json` output support.
4. Update README.md CLI table.

### Adding a new MCP tool

1. Add tool function in `server/mcp_tools.py`.
2. Register with `@mcp_tool` decorator.
3. Add tests.
4. Update README.md MCP tools table.

---

## Git workflow

- Fork `Joey-1123/impact_engine` and push branches to your fork.
- Pull requests target the `main` branch.
- Do not push directly to upstream unless explicitly authorized.

### Branch naming

```
fix/brain-method-detection
feat/new-biomarker
docs/update-readme
```

### Starting a branch

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git checkout -b feat/my-change
```

---

## Design decisions

- **Zero LLM for scoring**: health scores are deterministic from AST + git features. No cloud dependencies.
- **Plugin parsers**: language support via `core/parsers/` — Python is first-class, others are contrib.
- **NetworkX for graphs**: `nx.DiGraph` is the graph backend. No custom graph structures.
- **Rich for terminal**: `rich` library for formatted CLI output. No raw print for user-facing output.
- **FastAPI for API**: async endpoints with caching. Not Django REST for the API layer.
- **Django for web dashboard**: `impact_web/` is a separate Django app for the legacy web UI.

---

## Debug logging

- Use `logging` module with named loggers: `logging.getLogger("impact_engine.<module>")`.
- Default to `WARNING` level for CLI, `DEBUG` for `--verbose` flag.
- Log entry/exit for extraction, graph building, and scoring phases.
- Stable grep-friendly prefixes: `[extract]`, `[graph]`, `[health]`, `[kg]`.
- **Never** log secrets, API keys, or file contents.

---

## Coding philosophy

- **Unix-style modules**: small, single-responsibility, composed through clear boundaries.
- **Tests before the next layer**: untested code is incomplete.
- **Docs with code**: update AGENTS.md when rules or behavior change.
- **Self-hosting**: impact-engine analyzes itself. Keep the codebase clean enough to score well on its own biomarkers.
