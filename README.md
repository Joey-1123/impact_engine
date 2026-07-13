<div align="center">

<a href="https://github.com/Joey-1123/impact_engine"><img src=".github/assets/banner.svg" alt="Impact Engine: codebase intelligence platform" width="100%" /></a>

<p align="center"><strong>Dependency graph · Health scoring · Knowledge graph · MCP for AI agents · REST API · Web dashboard · One <code>pip install</code></strong></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-059669?style=for-the-badge&labelColor=0A0A0A" alt="License: MIT" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8%2B-1E293B?style=for-the-badge&labelColor=0A0A0A&logo=python&logoColor=white" alt="Python 3.8+" /></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-1E293B?style=for-the-badge&labelColor=0A0A0A" alt="MCP compatible" /></a>
  <a href="https://github.com/Joey-1123/impact_engine/stargazers"><img src="https://img.shields.io/github/stars/Joey-1123/impact_engine?style=for-the-badge&logo=github&color=1E293B&labelColor=0A0A0A&logoColor=white" alt="GitHub stars" /></a>
</p>

<p align="center"><sub>
  <a href="#intelligence-layers">Layers</a> ·
  <a href="#health-scoring">Health</a> ·
  <a href="#knowledge-graph">Knowledge Graph</a> ·
  <a href="#refactoring-intelligence">Refactoring</a> ·
  <a href="#supported-languages">Languages</a> ·
  <a href="#quick-start">Quickstart</a> ·
  <a href="#mcp-tools">MCP tools</a> ·
  <a href="#comparison">Comparison</a>
</sub></p>

---

<p align="center">
  <strong>measure, locate, and fix codebase risk before you ship</strong><br/>
  <strong>26 deterministic health biomarkers</strong> &nbsp;·&nbsp; <strong>zero LLM, zero cloud</strong> &nbsp;·&nbsp; <strong>under 30 seconds</strong> on a 3,000-file repo<br/>
  <strong>graph-aware refactoring plans</strong> your agent can execute &nbsp;·&nbsp; <strong>REST API</strong> &nbsp;·&nbsp; <strong>Web dashboard</strong> &nbsp;·&nbsp; <strong>MCP server</strong>
</p>

---

</div>

AI now writes a large and growing share of the code. The humans accountable for
what ships need to trust it. A score that says *"this file is risky"* isn't
enough — you need to know **where** the risk concentrates and **how** to fix it.

Impact Engine closes that loop. It indexes your codebase once and scores **every
file for defect risk, maintainability, and performance** from 26 deterministic
markers, no LLM, in under 30 seconds. The same index then **locates** the risk
through a real dependency graph and git history, and **generates the fix**:
concrete, graph-aware refactoring plans (split this god class, extract this
method, break this dependency cycle) that your coding agent can execute.

All exposed through a CLI, REST API, interactive web dashboard, and MCP server
for AI agent integration. One index: signals your team can trust, context your
agent can use, and the fix it can apply.

---

## Intelligence layers

Impact Engine runs once, builds everything, then keeps it in sync. Each layer is
queryable from the CLI, the MCP tools, and the web dashboard.

| Layer | What it gives you | Edge |
|---|---|---|
| **◈ Graph** | AST-level dependency graph · function + symbol nodes · call resolution · PageRank centrality · community detection · framework-aware edges | A real graph most tools never build |
| **◈ Git** | hotspots (churn × complexity) · ownership % · co-change pairs (hidden coupling) · bus factor · contributor profiles · module health | Behavioral signals static analysis can't see |
| **◈ Health** | **26 deterministic markers**, 1–10 per file · **three signals: defect risk · maintainability · performance** · coverage ingestion · trend tracking · **concrete graph-aware refactoring plans** (Extract Class / Extract Helper / Move Method / Break Cycle / Split File / Extract Method) · **zero LLM, <30s** | **★ Defect-validated, with the fix attached** |
| **◈ Decisions** | Architectural decisions mined from git history, ADRs, and changelogs, evidence-backed, linked to graph nodes | **★ Captured nowhere else** |
| **◈ Docs** | Auto-generated module documentation with dependency context · hybrid RAG search | Always in sync with your code |

---

## Health scoring

The deepest differentiator. Impact Engine scores **every file 1–10** from **26
deterministic markers**: McCabe complexity, brain methods, class cohesion
(LCOM4), god classes, Rabin–Karp clone detection, untested hotspots, change
entropy, prior-defect history, and more, split into **three signals**:

| Dimension | Biomarkers |
|---|---|
| **Defect risk** | Brain method, god class, complex method, nested complexity, primitive obsession, complex conditional, low cohesion, bumpy road, large class, DRY violation, error handling, untested hotspot, function hotspot, knowledge loss, churn risk, change entropy, co-change scatter, prior defect |
| **Maintainability** | All structural markers + ownership risk, developer congestion, coverage gap |
| **Performance** | IO-in-loop, string-concat-in-loop, blocking-sync-in-async |

- **Defect-calibrated**: weights learned from real bug data, not hand-tuned
- **Zero LLM**: pure Python over AST + git, under 30 seconds on a 3,000-file repo
- **Validated**: the score correlates with real defect history — low-health files
  receive significantly more bug fixes

```bash
impact-engine -p /path/to/project health --json
```

### Refactoring intelligence

A health score tells you a file is in trouble. Impact Engine names the
**specific** fix, computed deterministically from the graph, the class model,
and git co-change:

- **Extract Class** — LCOM4-splitting candidates
- **Extract Method** — dataflow-verified (CFG + def/use + reaching definitions)
- **Extract Helper** — co-change clusters that want a shared module
- **Move Method** — cross-class call dependencies
- **Break Cycle** — MFAS minimum-edge-cut on SCCs
- **Split File** — module-level cohesion analysis

Each plan carries its **blast radius** (the callers and co-changing files that
must move with it), ranked graph-aware.

```bash
impact-engine -p /path/to/project health --json   # includes refactoring targets
```

---

## Knowledge graph

Enriches the dependency graph with:

- **PageRank centrality** — identifies architecturally significant nodes
- **Community detection** — greedy modularity optimization reveals subsystem boundaries
- **Layer inference** — automatic classification into Application, Domain,
  Persistence, Presentation, Test, Config, and Utility layers
- **Entry-point tours** — guided walkthroughs from top-level entry points

```bash
impact-engine -p /path/to/project kg --json
```

---

## Duplication detection

Rabin-Karp rolling hash clone detection with token normalization. Identifies
exact and near-miss clones across the entire codebase. Per-file duplication
percentage feeds into the health scoring engine.

```bash
impact-engine -p /path/to/project duplication --json
```

---

## Decision mining

Extracts architectural design decisions from three sources:
- **Git log** — PR titles, commit messages with decision semantics
- **ADR files** — structured Architecture Decision Records from `docs/adr/`
- **Changelogs** — CHANGELOG.md / CHANGELOG.rst entries

Each decision carries a status (active, deprecated, superseded) and confidence
score based on evidence strength.

```bash
impact-engine -p /path/to/project decisions --source pr --json
```

---

## Local dashboard

`impact-engine serve` starts a full FastAPI web server alongside the MCP server.

| Endpoint | Description |
|---|---|
| `GET /health` | Service health check |
| `GET /api/repos/{id}/overview` | Repository metadata, language distribution, layers |
| `GET /api/repos/{id}/graph` | Knowledge graph with communities and centrality |
| `GET /api/repos/{id}/health-score` | 3D health scores with biomarker findings |
| `GET /api/repos/{id}/findings` | Filtered biomarker results |
| `GET /api/repos/{id}/decisions` | Mined architectural decisions |
| `GET /api/repos/{id}/costs` | LLM generation cost estimates |

The Next.js web dashboard provides interactive exploration of all layers:
**Overview** · **Graph** (community-colored, 2,000+ nodes, path finding) ·
**Decisions** · **Health** (three signals, trends).

```bash
# Terminal 1: API server
impact-engine -p /path/to/project serve --port 8000

# Terminal 2: Web dashboard
cd web && npm run dev
```

---

## AI agent integration (MCP)

Model Context Protocol server exposing all intelligence layers to AI coding
agents. Configure in your agent's MCP settings:

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

### Nine MCP tools

| Tool | What it answers |
|---|---|
| `get_overview()` | Architecture summary, module map, entry points, layer distribution |
| `get_health()` | 3D health scores, biomarker findings, refactoring targets |
| `get_graph()` | Knowledge graph nodes, edges, communities, centrality |
| `get_dead_code()` | Unreachable code by confidence tier with cleanup impact |
| `get_decisions()` | Architectural decision records with status and evidence |
| `get_duplication()` | Clone pairs across the codebase |
| `get_cost_estimate()` | LLM generation cost per page type and model |
| `get_findings()` | Filtered biomarker results by category and severity |
| `list_tools()` | Available tool discovery |

---

## CLI reference

| Command | Description |
|---|---|
| `analyze` | Full analysis pipeline |
| `graph` | Terminal dependency graph |
| `summary` | Ranked risk hotspot report |
| `impact <func>` | What breaks if a function changes |
| `predict <func>` | What-if simulation without git |
| `health` | 3D health score with biomarkers |
| `kg` | Knowledge graph with layers |
| `decisions` | Design decision mining |
| `cost` | LLM generation cost estimation |
| `duplication` | Code clone detection |
| `cycles` | Circular dependency detection |
| `complexity` | Cyclomatic complexity ranking |
| `diff` | Working tree changes |
| `compare` | Branch risk delta |
| `mermaid` | Mermaid.js diagram export |
| `sarif` | GitHub code scanning SARIF export |
| `html` | Interactive D3.js HTML report |
| `pre-commit` | Pre-commit risk check |
| `watch` / `iwatch` | Continuous file watching |
| `serve` | FastAPI REST server |
| `mcp` | MCP server for AI agents |

All analysis commands support `--json` for structured output.

---

## Supported languages

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black" alt="JavaScript" />
  <img src="https://img.shields.io/badge/Java-ED8B00?style=flat-square&logo=openjdk&logoColor=white" alt="Java" />
  <img src="https://img.shields.io/badge/Go-00ADD8?style=flat-square&logo=go&logoColor=white" alt="Go" />
  <img src="https://img.shields.io/badge/Rust-000000?style=flat-square&logo=rust&logoColor=white" alt="Rust" />
  <img src="https://img.shields.io/badge/C++-00599C?style=flat-square&logo=cplusplus&logoColor=white" alt="C++" />
  <img src="https://img.shields.io/badge/Swift-F05138?style=flat-square&logo=swift&logoColor=white" alt="Swift" />
  <img src="https://img.shields.io/badge/PHP-777BB4?style=flat-square&logo=php&logoColor=white" alt="PHP" />
  <img src="https://img.shields.io/badge/Zig-F7A41D?style=flat-square&logo=zig&logoColor=white" alt="Zig" />
</p>

Python (AST) is the **Full tier** with all 26 health biomarkers. Other languages
use plugin parsers with import resolution, call tracking, and basic complexity
scoring.

---

## Architecture

```
Parse ──► Graph ──► Analyze ──► Enrich ──► Serve
  │           │           │            │           │
  ▼           ▼           ▼            ▼           ▼
AST        nx.DiGraph   Dead Code    Knowledge   FastAPI /
Extraction             Cycles       Graph       Next.js /
+ Line                  Entry Pts    Decision    MCP
Numbers                 Health       Mining
+ CCN                   Scoring
```

1. **Parse** — AST-based extraction of function definitions, calls, imports,
   decorators, and class hierarchies with line number tracking and complexity
2. **Graph** — `networkx.DiGraph` with typed edges at function granularity
3. **Analyze** — Dead code, cycles, entry points, 26 health biomarkers
4. **Enrich** — Knowledge graph (PageRank + communities + layers), decision mining
5. **Serve** — CLI, REST API (FastAPI), Web UI (Next.js 15), MCP (FastMCP)

---

## Comparison

| | Impact Engine | CodeScene | DeepWiki | Swimm |
|---|---|---|---|---|
| Self-hostable, open source | ✅ MIT | ✅ Docker | ❌ cloud only | ❌ Enterprise only |
| Private repo, no cloud | ✅ | ✅ | ❌ OSS forks only | ✅ Enterprise tier |
| MCP server for AI agents | ✅ 9 tools | ✅ | ✅ 3 tools | ✅ |
| Code health score (1-10) | ✅ 26 markers | ✅ 25-30 | ❌ | ❌ |
| Brain Method / LCOM4 / god class | ✅ | ✅ | ❌ | ❌ |
| Test-coverage intelligence | ✅ LCOV/Cobertura | ❌ | ❌ | ❌ |
| Refactoring recommendations | ✅ deterministic | ✅ | ❌ | ❌ |
| Concrete cross-file refactoring plans | ✅ graph-aware + blast radius | ⚠️ within-function only | ❌ | ❌ |
| Git intelligence (hotspots, ownership, co-change) | ✅ | ✅ | ❌ | ❌ |
| Dead code detection | ✅ | ❌ | ❌ | ❌ |
| Architectural decision records | ✅ | ❌ | ❌ | ❌ |
| Local dashboard | ✅ | ✅ IDE only | ❌ | ✅ |

---

## Quick start

```bash
# Install
pip install impact-engine
pip install rich fastapi uvicorn mcp lancedb

# Analyze any Python project
impact-engine -p /path/to/project analyze

# Health score with biomarkers
impact-engine -p /path/to/project health --json

# Knowledge graph
impact-engine -p /path/to/project kg --json

# Code clone detection
impact-engine -p /path/to/project duplication

# REST API server
impact-engine -p /path/to/project serve --port 8000

# AI agent MCP server
impact-engine -p /path/to/project mcp --port 8001
```

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

Full setup guide including web UI: [INSTALL.md](INSTALL.md).

---

## Project structure

```
impact_engine/
├── cli/                     # CLI entry point (25+ commands, argparse)
├── core/
│   ├── health/              # Scoring engine + 26 biomarker detectors
│   ├── graph/               # Knowledge graph (PageRank, communities)
│   ├── providers/           # LLM (OpenAI, Anthropic, Gemini) + embedders
│   ├── persistence/         # Vector store (InMemory, LanceDB)
│   └── pipeline/            # Analysis orchestrator
├── server/                  # FastAPI + MCP servers, 7 routers
├── web/                     # Next.js 15 dashboard (4 pages)
└── tests/
```

---

## License

MIT License — see [LICENSE](LICENSE).

Built by Shubham Panchal (Joey) · [GitHub](https://github.com/Joey-1123)
