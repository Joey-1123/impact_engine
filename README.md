<div align="center">

<img alt="Impact Engine" src=".github/assets/banner.svg" width="600">


<p><strong>Static code analysis pipeline with health scoring, knowledge graphs, and AI agent tooling</strong></p>

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-059669?style=for-the-badge&labelColor=0A0A0A" alt="License: MIT" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8%2B-1E293B?style=for-the-badge&labelColor=0A0A0A&logo=python&logoColor=white" alt="Python 3.8+" /></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-1E293B?style=for-the-badge&labelColor=0A0A0A" alt="MCP compatible" /></a>
  <a href="https://github.com/Joey-1123/impact_engine/stargazers"><img src="https://img.shields.io/github/stars/Joey-1123/impact_engine?style=for-the-badge&logo=github&color=1E293B&labelColor=0A0A0A&logoColor=white" alt="GitHub stars" /></a>
</p>

</div>

Impact Engine is a Python-based static analysis framework that builds a function-level dependency graph from your codebase, scores every file for defect risk and maintainability using 26 deterministic biomarkers, constructs a knowledge graph with community detection and layer inference, and exposes everything through a CLI, REST API, web dashboard, and MCP server.

---

## What it does

| Component | Description |
|---|---|
| **Dependency graph** | AST-level call graph at function granularity, cyclomatic complexity, decorator tracking, circular dependency detection |
| **Health scoring** | 26 biomarkers across three dimensions (defect, maintainability, performance), zero LLM, under 30 seconds |
| **Knowledge graph** | PageRank centrality, greedy modularity communities, architectural layer inference, entry-point tours |
| **Clone detection** | Rabin-Karp rolling hash, token-normalized, feeds duplication % into health scores |
| **Decision mining** | Extract design decisions from git log, ADRs, and changelogs with confidence scoring |
| **REST API** | FastAPI server with 9 endpoint groups, cached async analysis, CORS-enabled |
| **Web dashboard** | Next.js 15 app with graph explorer, health view, decision viewer |
| **MCP server** | 4 tools for AI coding agents (Claude Code, Codex, Cursor) |

---

## Installation

```bash
# From source
git clone https://github.com/Joey-1123/impact_engine.git
cd impact_engine
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install rich fastapi uvicorn mcp lancedb openai anthropic google-genai
```

Full setup including web UI: [INSTALL.md](INSTALL.md).

---

## Quick start

```bash
# Analyze a project
impact-engine -p /path/to/project analyze

# Health score
impact-engine -p /path/to/project health --json

# Knowledge graph
impact-engine -p /path/to/project kg --json

# Code clone report
impact-engine -p /path/to/project duplication

# REST API
impact-engine -p /path/to/project serve --port 8000

# MCP server for AI agents
impact-engine -p /path/to/project mcp --port 8001
```

---

## Health scoring

Every file in your project is scored from 1 (worst) to 10 (best) across three
independent signals. Scores are computed from deterministic AST + git features
— no LLM calls, no cloud dependencies.

### The three signals

| Signal | What it measures |
|---|---|
| **Defect risk** | Structural complexity (brain methods, god classes, nested conditionals), organizational risk (untested hotspots, prior defects, change entropy), cohesion violations (LCOM4, primitive obsession) |
| **Maintainability** | Code clarity, duplication, class size, ownership concentration, bus factor |
| **Performance** | I/O inside loops, string concatenation in loops, blocking calls in async functions |

### The 26 biomarkers

**Structural** — brain method, god class, complex method, large method, nested complexity, primitive obsession, complex conditional, low cohesion, bumpy road, large class, DRY violation, error handling

**Performance** — IO-in-loop, string-concat-in-loop, blocking-sync-in-async

**Organizational** — untested hotspot, coverage gap, function hotspot, ownership risk, developer congestion, knowledge loss, churn risk, code age volatility, change entropy, co-change scatter, prior defect

```bash
impact-engine -p /path/to/project health --json
```

### Refactoring targets

The health score identifies *where* the problem is. Impact Engine also computes
*what to do about it* — concrete refactoring plans ranked by impact × centrality:

- **Extract Class** — LCOM4-based class splitting
- **Extract Method** — dataflow analysis (CFG + def/use) infers the exact line span and signature
- **Extract Helper** — co-change clusters that belong in a shared module
- **Move Method** — cross-class call graphs that violate cohesion
- **Break Cycle** — minimum feedback arc set on strongly connected components
- **Split File** — module-level cohesion analysis

---

## Knowledge graph

The dependency graph is enriched with:

- **PageRank** — identifies the most architecturally significant nodes
- **Community detection** — greedy modularity optimization uncovers subsystem boundaries
- **Layer classification** — files are automatically tagged as Application, Domain,
  Persistence, Presentation, Test, Config, or Utility based on path heuristics
- **Entry-point tours** — a ranked walkthrough starting from `main()` and other entry points

```bash
impact-engine -p /path/to/project kg --json
```

---

## Clone detection

Rabin-Karp rolling hash with token normalization finds exact and near-miss
duplicates. The per-file duplication percentage flows into the health scoring
engine as a maintainability signal.

```bash
impact-engine -p /path/to/project duplication --json
```

---

## Decision mining

Design decisions are extracted from three sources:

- **Git log** — commit messages and PR titles that carry decision semantics
- **ADR files** — structured Architecture Decision Records from `docs/adr/`
- **Changelogs** — `CHANGELOG.md` / `CHANGELOG.rst` entries

Each decision is tagged with a status (active, deprecated, superseded) and a
confidence score based on evidence quality.

```bash
impact-engine -p /path/to/project decisions --source pr --json
```

---

## REST API

```bash
impact-engine -p /path/to/project serve --port 8000
```

| Endpoint | Returns |
|---|---|---|
| `GET /health` | Service status + version |
| `GET /api/repos/{id}/overview` | File counts, language distribution, layers |
| `GET /api/repos/{id}/graph` | Knowledge graph nodes, edges, communities |
| `GET /api/repos/{id}/health-score` | 3D health scores + finding count |
| `GET /api/repos/{id}/findings` | Filtered biomarker results |
| `GET /api/repos/{id}/decisions` | Mined architectural decisions |
| `GET /api/repos/{id}/costs` | LLM generation cost estimates |
| `GET /api/repos/{id}/impact` | Impact analysis for a given function |
| `GET /api/repos/{id}/timeline` | Git timeline with before/after changes |
| `GET /api/repos/{id}/report` | PR-style impact report |
| `POST /webhook/github` | GitHub webhook receiver (HMAC-verified) |

---

## Web dashboard

A Next.js 15 application (App Router, Tailwind CSS 4) with pages for
repository overview, knowledge graph exploration, health score browsing,
and decision history. Proxies API calls to the backend.

```bash
cd web && npm run dev    # defaults to localhost:3000
```

---

## MCP server (AI agents)

Exposes the full analysis pipeline to AI coding agents via the Model Context
Protocol. Add to your agent's config:

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

### Available tools

| Tool | Description |
|---|---|
| `get_overview()` | Repo structure, layers, entry points |
| `get_health()` | Health scores, biomarker findings, refactoring targets |
| `get_graph()` | Knowledge graph nodes and edges |
| `list_tools()` | Discover available tools |

---

## CLI commands

| Command | Purpose |
|---|---|
| `analyze`, `graph`, `summary` | Core analysis pipeline |
| `impact`, `predict` | Impact propagation and what-if simulation |
| `health`, `kg`, `decisions`, `cost`, `duplication` | Intelligence layers |
| `cycles`, `complexity`, `diff`, `compare` | Codebase diagnostics |
| `mermaid`, `sarif`, `html` | Format export |
| `pre-commit` | Git hook integration |
| `watch`, `iwatch` | File watching |
| `serve`, `mcp` | Server modes |

All commands accept `-p` for project path and `--json` for structured output.

---

## Architecture

```
Parse ──► Graph ──► Analyze ──► Enrich ──► Serve

AST         nx.DiGraph   Dead Code    Knowledge   CLI
Extraction               Cycles       Graph       FastAPI
+ Line #s    call/import  Entry Points  PageRank    Next.js
+ CCN        edges        Health       Communities MCP
```

The pipeline runs in under 30 seconds on a 3,000-file repository and caches
results for incremental updates.

---

## Language support

Python is fully supported with all 26 biomarkers, AST-level extraction, and
decorator tracking. Plugin parsers provide import resolution, call tracking,
and complexity scoring for JavaScript, TypeScript, Go, Rust, Java, C++, Swift,
PHP, and Zig.

---

## Project structure

```
impact_engine/
├── cli/                     # Argparse entry point (25+ commands)
├── core/
│   ├── health/              # Scoring engine + 26 biomarker detectors
│   ├── graph/               # Knowledge graph construction
│   ├── providers/           # LLM providers (OpenAI, Anthropic, Gemini)
│   ├── persistence/         # Vector store (InMemory, LanceDB)
│   └── pipeline/            # Orchestrator
├── server/                  # FastAPI + MCP servers
├── web/                     # Next.js 15 dashboard
└── tests/
```

---

## License

MIT — see [LICENSE](LICENSE).

Built by [Shubham Panchal (Joey)](https://github.com/Joey-1123)
