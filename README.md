# Impact Engine

<div align="center">
  <p><b>Codebase intelligence platform — dependency graph, health scoring, knowledge graph, and REST API.</b></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
</div>

---

## What is Impact Engine?

Impact Engine parses your codebase, builds a directed dependency graph, and provides **health scoring**, **knowledge graph**, **clone detection**, **decision mining**, **cost estimation**, and a **REST API** + **web dashboard** for interactive exploration.

---

## Features

### Core Analysis
- **Dependency Graphing** — Full call-graph extraction at function granularity (Python AST)
- **Impact Analysis** — `impact-engine impact <func>` shows every affected downstream
- **What-If Analysis** — `impact-engine predict <func>` simulates changes without touching git
- **Dead Code Detection** — Functions unreachable from entry points
- **Circular Dependency Detection** — `impact-engine cycles`
- **Cyclomatic Complexity** — McCabe score ranking
- **Test Impact Mapping** — `--test-only` flag filters to affected tests
- **Decorator Tracking** — `@app.route(...)` tracked as dependencies
- **Multi-Language** — Plugin parsers for Python, JS/TS, Rust, Go, Java
- **CI/CD Ready** — Structured JSON output (`--json`) for GitHub Actions
- **Pre-Commit Hook** — `impact-engine pre-commit` blocks risky commits

### Health Scoring
- **3D Health Score** — defect, maintainability, and performance dimensions
- **26 Biomarker Detectors** — structural (brain method, god class, complex method, low cohesion, nested complexity, primitive obsession, complex conditional, bumpy road, large class, DRY violation, error handling), performance (IO-in-loop, string-concat-in-loop, blocking-sync-in-async), organizational (untested hotspot, coverage gap, function hotspot, ownership risk, developer congestion, knowledge loss, churn risk, code age volatility, change entropy, co-change scatter, prior defect)
- **Weighted Scoring Engine** — calibrated weights per dimension, per-category caps
- **CLI**: `impact-engine -p <path> health [--json]`

### Knowledge Graph
- **Automatic Layer Inference** — Application, Utility, Domain, Persistence, Presentation, Test, Config
- **PageRank** — centrality scoring for all nodes
- **Community Detection** — greedy modularity optimization
- **Entry-Point Tours** — guided walkthrough from top-level entry points
- **CLI**: `impact-engine -p <path> kg [--json]`

### Duplication Detection
- **Rabin-Karp Rolling Hash** — token-normalized clone detection
- **Per-file duplication percentage** feeds into health scoring
- **CLI**: `impact-engine -p <path> duplication [--json]`

### Decision Mining
- Extract design decisions from `git log`, ADR files, and changelogs
- **CLI**: `impact-engine -p <path> decisions --source pr|adr|changelog [--json]`

### Cost Estimation
- Heuristic token costing per page type across 7 models (Claude, GPT, Gemini)
- **CLI**: `impact-engine cost --types file_summary,tour_step --count 5 --model gpt-4o`

### FastAPI Server
- **7 routers** — health, overview, graph, health-score, costs, decisions, workspace
- **Caching** — `repo_worker.py` caches analysis per repo path
- **CLI**: `impact-engine -p <path> serve --port 8000`

### Web UI (Next.js 15)
- **4 pages** — dashboard, repo overview, graph explorer, decision viewer
- **Tailwind CSS 4**, App Router
- **CLI**: `cd web && npm run dev` (proxies to backend at :8000)

### MCP Server (AI Agent Integration)
- **4 tools** — `get_overview`, `get_health`, `get_graph`, `list_tools`
- **FastMCP** with SSE transport
- **CLI**: `impact-engine -p <path> mcp --port 8001`

### LLM Providers
- **Async providers** — OpenAI, Anthropic, Gemini
- **Embedders** — OpenAI text-embedding
- **Extensible registry** — `register_provider()`, `get_provider()`
- **Mock provider** for testing

### Vector Stores
- **ABC** with `InMemoryVectorStore` (dev) and `LanceDBVectorStore` (production)
- Cosine similarity search

### Additional CLI Tools
| Command | Description |
|---------|-------------|
| `mermaid` | Export Mermaid.js diagram |
| `sarif` | Export GitHub code scanning SARIF |
| `html` | Interactive D3.js HTML report |
| `compare` | Risk delta between branches |
| `watch` / `iwatch` | Continuous file watching |
| `diff` | Working tree changes |
| `complexity` | Complexity ranking |

---

## Installation

```bash
git clone https://github.com/Joey-1123/impact_engine.git
cd impact_engine

python -m venv .venv
source .venv/bin/activate

pip install -e .
pip install rich fastapi uvicorn mcp lancedb openai anthropic google-genai
```

See [INSTALL.md](INSTALL.md) for detailed setup including Web UI.

---

## Quick Start

```bash
# Analyze a project
impact-engine -p /path/to/project analyze

# Health score
impact-engine -p /path/to/project health

# Knowledge graph
impact-engine -p /path/to/project kg

# Clone detection
impact-engine -p /path/to/project duplication

# Start REST API
impact-engine -p /path/to/project serve --port 8000
```

---

## Project Structure

```
impact_engine/
├── cli/
│   ├── main.py              # CLI entry point (25+ commands, argparse)
│   └── new_commands.py      # Health, KG, decisions, cost, duplication, serve, MCP
├── core/
│   ├── extractor.py         # AST dependency extraction
│   ├── graph_builder.py     # NetworkX directed graph
│   ├── traversal.py         # BFS impact propagation
│   ├── analyzer.py          # Risk scoring + dead code
│   ├── detector.py          # Cycle detection + entry points
│   ├── git_analyzer.py      # Git diff → changed functions
│   ├── git_blame.py         # Function-level blame index
│   ├── layer_inference.py   # Architectural layer detection
│   ├── decisions.py         # Decision mining (PR, ADR, changelog)
│   ├── cost_estimator.py    # LLM generation cost estimation
│   ├── workspace.py         # Multi-repo workspace config
│   ├── registry.py          # MCP tool registry
│   ├── health/
│   │   ├── scoring.py       # 3D scoring engine (defect, maint, perf)
│   │   ├── duplication.py   # Rabin-Karp clone detection
│   │   ├── refactoring.py   # Refactoring detectors
│   │   ├── validation.py    # Defect accuracy self-validation
│   │   └── biomarkers/      # 26 biomarker detectors
│   │       ├── _models.py
│   │       ├── _base.py
│   │       ├── structural.py
│   │       ├── performance.py
│   │       └── organizational.py
│   ├── graph/
│   │   └── kg.py            # Knowledge Graph (PageRank, communities, layers)
│   ├── providers/
│   │   ├── base.py          # BaseProvider ABC, ChatProvider, Embedder
│   │   ├── registry.py      # Provider registration
│   │   ├── mock.py          # MockProvider, MockEmbedder
│   │   ├── llm/             # OpenAI, Anthropic, Gemini providers
│   │   └── embedding/       # OpenAI embedder
│   ├── persistence/
│   │   └── vector_store/    # VectorStore ABC + InMemory + LanceDB backends
│   └── pipeline/            # Pipeline orchestrator
├── server/
│   ├── app.py               # FastAPI app factory
│   ├── mcp_server.py        # FastMCP server
│   ├── repo_worker.py       # Cached async analysis
│   ├── schemas.py           # Pydantic/dataclass response models
│   └── routers/             # 7 routers (health, overview, graph, etc.)
├── web/                     # Next.js 15 web UI
│   ├── src/app/             # App Router pages
│   └── package.json
└── tests/                   # Test suite
```

---

## Architecture

1. **Parse** — AST extraction with line numbers and cyclomatic complexity
2. **Graph** — `networkx.DiGraph` with caller→callee edges
3. **Analyze** — Dead code, cycles, entry points, health scoring
4. **Enrich** — Knowledge graph (PageRank + community detection), decision mining
5. **Serve** — FastAPI REST API + Next.js web UI + MCP server

---

## License

MIT License — see [LICENSE](LICENSE).

Built by Shubham Panchal (Joey)
