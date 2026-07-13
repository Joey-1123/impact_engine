# Impact Engine

<div align="center">
  <p><b>Enterprise codebase intelligence platform — dependency analysis, health scoring, knowledge graphs, and AI integration.</b></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
</div>

Impact Engine provides engineering organizations with deep visibility into codebase health, dependency structure, and technical risk — enabling data-driven decisions at scale.

---

## Overview

Engineering leaders face a fundamental challenge: understanding the structural health, risk posture, and maintainability trajectory of large codebases. Impact Engine solves this through a multi-dimensional analysis platform that combines static dependency analysis, health biomarker scoring, knowledge graph construction, and AI-powered enrichment — all exposed through a CLI, REST API, web dashboard, and MCP server for AI agent integration.

### Key Capabilities

| Capability | Description |
|---|---|
| **Dependency Graph** | Function-level call graph extraction via Python AST with cyclomatic complexity scoring |
| **Health Scoring** | 26 deterministic biomarker detectors across defect, maintainability, and performance dimensions |
| **Knowledge Graph** | PageRank centrality, community detection, architectural layer inference, entry-point tours |
| **Clone Detection** | Rabin-Karp rolling hash duplication analysis at scale |
| **Decision Mining** | Automated extraction of design decisions from git history, ADRs, and changelogs |
| **REST API** | FastAPI server with 7 router groups and cached async analysis |
| **Web Dashboard** | Next.js 15 application with interactive graph exploration |
| **AI Integration** | MCP server (Model Context Protocol) for AI coding agent tool access |
| **LLM Providers** | First-class support for OpenAI, Anthropic, and Gemini with extensible provider registry |
| **Vector Store** | Embedding-based semantic search with InMemory and LanceDB backends |

---

## Use Cases

- **Engineering Due Diligence** — Assess codebase health before acquisitions or large-scale migrations
- **Refactoring Prioritization** — Identify hotspots with the highest defect risk and maintenance burden
- **Technical Debt Tracking** — Monitor health score trends over time across releases
- **Change Risk Assessment** — Evaluate blast radius and propagation risk before shipping changes
- **Developer Onboarding** — Generate knowledge graph tours that guide new engineers through system architecture
- **AI Agent Enablement** — Expose codebase intelligence to AI coding agents via standardized MCP tool interface

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

See [INSTALL.md](INSTALL.md) for complete setup instructions including web UI and MCP server configuration.

---

## Quick Start

```bash
# Full analysis pipeline
impact-engine -p /path/to/project analyze

# Health score with biomarker detection
impact-engine -p /path/to/project health --json

# Knowledge graph with architectural layers
impact-engine -p /path/to/project kg --json

# Code clone detection
impact-engine -p /path/to/project duplication

# REST API server
impact-engine -p /path/to/project serve --port 8000

# AI agent MCP server
impact-engine -p /path/to/project mcp --port 8001
```

---

## Architecture

```
Parse ──► Graph ──► Analyze ──► Enrich ──► Serve
  │           │           │            │           │
  ▼           ▼           ▼            ▼           ▼
AST        nx.DiGraph   Dead Code    Knowledge   FastAPI /
Extraction             Cycles       Graph       Next.js /
+ Line                 Entry Pts    Decision    MCP
Numbers                Health       Mining
+ CCN                  Scoring
```

### Core Analysis Pipeline

The platform processes code through five stages:

1. **Parse** — AST-based extraction of function definitions, calls, imports, decorators, and class hierarchies with line number tracking and cyclomatic complexity scoring
2. **Graph** — Construction of a `networkx.DiGraph` with typed edges (call, import, decorate, inherit) at function granularity
3. **Analyze** — Multi-dimensional analysis: dead code detection from entry-point reachability, circular dependency detection via DFS, health biomarker evaluation across 26 detectors
4. **Enrich** — Knowledge graph construction with PageRank centrality, community detection (greedy modularity), architectural layer inference, and decision mining from git history
5. **Serve** — Multi-channel access: CLI (argparse, 25+ commands), REST API (FastAPI, 7 routers), interactive dashboard (Next.js 15), and MCP server (FastMCP, 4 tools)

---

## Platform Components

### Dependency Graph Engine

The core analysis engine performs function-level dependency extraction across Python codebases, producing a directed graph with cyclomatic complexity annotations per node. Supports impact analysis (what breaks if a function changes), dead code detection, circular dependency detection, and what-if simulation.

### Health Scoring System

A deterministic scoring engine evaluates codebase health across three dimensions using 26 biomarker detectors:

| Dimension | Biomarkers |
|---|---|
| **Structural** | Brain method, god class, complex method, large method, nested complexity, primitive obsession, complex conditional, low cohesion, bumpy road, large class, DRY violation, error handling |
| **Performance** | IO-in-loop, string-concat-in-loop, blocking-sync-in-async |
| **Organizational** | Untested hotspot, coverage gap, function hotspot, ownership risk, developer congestion, knowledge loss, churn risk, code age volatility, change entropy, co-change scatter, prior defect |

Each biomarker produces a weighted deduction capped per category. The engine outputs per-dimension scores (1-10) with detailed findings suitable for CI/CD integration and trend tracking.

### Knowledge Graph

Constructs an enriched knowledge representation from the dependency graph featuring:
- **PageRank centrality** — identifies architecturally significant nodes
- **Community detection** — greedy modularity optimization reveals subsystem boundaries
- **Layer inference** — automatic classification into Application, Domain, Persistence, Presentation, Test, Config, and Utility layers
- **Entry-point tours** — guided walkthroughs from top-level entry points

### REST API

FastAPI server with seven router groups:

| Endpoint | Description |
|---|---|
| `GET /health` | Service health check with version |
| `GET /api/repos/{id}/overview` | Repository metadata and language distribution |
| `GET /api/repos/{id}/graph` | Knowledge graph with layers, communities, and centrality |
| `GET /api/repos/{id}/health-score` | Multi-dimensional health scores with findings |
| `GET /api/repos/{id}/findings` | Filtered biomarker findings |
| `GET /api/repos/{id}/decisions` | Mined design decisions |
| `GET /api/repos/{id}/costs` | LLM generation cost estimates |

### Web Dashboard

Next.js 15 application with App Router, Tailwind CSS 4, featuring dashboard, repository overview, knowledge graph explorer, and decision viewer. Proxies analysis requests to the FastAPI backend.

### MCP Server

Model Context Protocol server exposing codebase intelligence to AI coding agents via four tools:
- `get_overview` — Repository structure and layer distribution
- `get_health` — Health score and biomarker findings
- `get_graph` — Knowledge graph data
- `list_tools` — Available tool discovery

### LLM Provider Layer

Extensible async provider system with first-class support for OpenAI, Anthropic, and Gemini. Includes text embedding via OpenAI's embedding API. Custom provider registration via `register_provider()` and `register_embedder()`.

### Vector Store

Abstract vector store interface with two production backends:
- **InMemoryVectorStore** — Development and single-user scenarios
- **LanceDBVectorStore** — Embedded persistent storage with merge_insert semantics

---

## CLI Reference

| Command | Description |
|---|---|
| `analyze` | Full analysis pipeline |
| `graph` | Terminal dependency graph visualization |
| `summary` | Ranked risk hotspot report |
| `health` | 3D health score with biomarkers |
| `kg` | Knowledge graph with layers and tours |
| `decisions` | Design decision mining |
| `cost` | LLM generation cost estimation |
| `duplication` | Code clone detection |
| `impact` | Change impact propagation |
| `predict` | What-if simulation |
| `cycles` | Circular dependency detection |
| `complexity` | Cyclomatic complexity ranking |
| `diff` | Working tree analysis |
| `compare` | Branch risk delta |
| `mermaid` | Mermaid.js diagram export |
| `sarif` | GitHub code scanning SARIF export |
| `html` | Interactive D3.js report |
| `pre-commit` | Pre-commit risk check |
| `watch` / `iwatch` | Continuous file monitoring |
| `serve` | FastAPI REST server |
| `mcp` | MCP server for AI agents |

All analysis commands support `--json` for structured output.

---

## Integration

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Codebase Health Check
  run: |
    impact-engine -p . health --json > health-report.json
    impact-engine -p . duplication --json >> health-report.json
```

### AI Agent Configuration

```json
{
  "mcpServers": {
    "impact-engine": {
      "command": "impact-engine",
      "args": ["-p", "/path/to/project", "mcp", "--port", "8001"]
    }
  }
}
```

### VS Code Integration

MCP server can be configured as a VS Code extension tool source for inline codebase intelligence.

---

## Project Structure

```
impact_engine/
├── cli/                     # CLI entry point and command handlers
├── core/                    # Analysis engine
│   ├── health/              # Scoring engine + 26 biomarker detectors
│   ├── graph/               # Knowledge graph construction
│   ├── providers/           # LLM and embedding provider layer
│   ├── persistence/         # Vector store backends
│   └── pipeline/            # Analysis orchestrator
├── server/                  # FastAPI + MCP servers
│   └── routers/             # 7 API router groups
├── web/                     # Next.js 15 dashboard
└── tests/
```

---

## License

MIT License — see [LICENSE](LICENSE).

Built by Shubham Panchal (Joey)
