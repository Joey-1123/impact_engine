# Impact Engine — Installation

## Prerequisites

| Dependency | Version | Required For |
|-----------|---------|-------------|
| Python | ≥ 3.8 | Core analysis, CLI, server |
| Node.js | ≥ 20 | Web UI (optional) |
| npm | ≥ 9 | Web UI (optional) |

## 1. Install the Python Package

### From source (recommended)

```bash
git clone <your-repo-url> impact_engine
cd impact_engine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install core dependencies
pip install networkx pathspec

# Install extras based on your needs:
pip install rich           # Colored terminal output (recommended)
pip install fastapi uvicorn mcp  # Server + MCP mode
pip install graphviz       # Visual graph export
pip install watchdog       # File watching mode
pip install click          # CLI (fallback if setuptools entry point unavailable)
```

### Verify installation

```bash
impact-engine --version
# Or if entry point isn't registered:
python -m cli.main --version
```

## 2. Install the Web UI (optional)

```bash
cd web
npm install
npm run build       # Production build
npm run dev         # Development server on :3000
```

The Web UI proxies API calls to the Impact Engine server (default `http://localhost:8000`). Set `IMPACT_API_URL` to override.

## 3. Quick Start

```bash
# Analyze any Python project
impact-engine -p /path/to/your/project analyze

# Health score with 23 biomarkers
impact-engine -p /path/to/your/project health

# Knowledge graph
impact-engine -p /path/to/your/project kg

# Code clone detection
impact-engine -p /path/to/your/project duplication

# Start REST API
impact-engine -p /path/to/your/project serve --port 8000

# Start MCP server (for AI agent integration)
impact-engine -p /path/to/your/project mcp --port 8001
```

## 4. Available Commands

| Command | Description |
|---------|-------------|
| `analyze` | Full analysis: graph, dead code, cycles, complexity |
| `graph` | Terminal dependency graph |
| `summary` | Ranked risk hotspots |
| `impact <func>` | What breaks if a function changes |
| `diff` | Current working tree changes |
| `complexity` | Cyclomatic complexity ranking |
| `health` | 3D health score (26 biomarkers, zero LLM) |
| `kg` | Knowledge graph with layers, PageRank, communities |
| `decisions` | Mine design decisions from git log, ADRs, changelogs |
| `cost` | Estimate LLM generation cost |
| `duplication` | Detect code clones (Rabin-Karp rolling hash) |
| `cycles` | Find circular dependencies |
| `mermaid` | Export Mermaid.js diagram |
| `sarif` | Export SARIF (GitHub code scanning) |
| `html` | Interactive D3.js HTML report |
| `serve` | Start FastAPI server (REST API + webhook) |
| `mcp` | Start MCP server for AI agents |
| `compare` | Risk delta between branches |
| `pre-commit` | Check staged files against risk threshold |
| `predict` | What-if simulation (no git needed) |
| `watch` / `iwatch` | File watching (full / incremental) |

## 5. Configuration

Create `.impactrc` in your project root (optional):

```json
{
  "max_depth": 3,
  "max_children": 12,
  "limit": 10,
  "respect_gitignore": true
}
```

Or use CLI flags: `--depth`, `--children`, `--limit`, `--json`.

## 6. Server Setup

```bash
# Start server (provides REST API at :8000)
impact-engine -p /path/to/project serve --host 127.0.0.1 --port 8000

# API endpoints:
# GET  /health
# GET  /api/repos/{id}/overview
# GET  /api/repos/{id}/graph
# GET  /api/repos/{id}/health-score
# GET  /api/repos/{id}/findings
# GET  /api/repos/{id}/costs
# GET  /api/repos/{id}/decisions
# GET  /api/repos/{id}/impact?function=<name>
# GET  /api/repos/{id}/timeline
# GET  /api/repos/{id}/report
# POST /webhook/github
# GET  /workspace
# GET  /workspace/graph
# GET  /workspace/conformance
```

## 7. Web UI

```bash
# Terminal 1: Start the API server
impact-engine -p /path/to/project serve

# Terminal 2: Start the Next.js dev server
cd web && npm run dev

# Open http://localhost:3000
```

## 8. MCP Server (AI Agent Integration)

```bash
impact-engine -p /path/to/project mcp --port 8001
```

Available MCP tools: `get_overview`, `get_health`, `get_graph`, `list_tools`.

## 9. Running Tests

```bash
# Import smoke test
python -c "
import sys; sys.path.insert(0, '.')
from core.pipeline import run_pipeline
from core.health import score_file
from core.git_blame import BlameIndex
from core.health.duplication import find_clones
from core.graph.kg import build_knowledge_graph_skeleton
from server.app import create_app
print('All modules OK')
"

# Run against self
impact-engine -p . health
impact-engine -p . duplication
```

## 10. Uninstall

```bash
pip uninstall impact-engine
rm -rf web/node_modules web/.next
rm -rf .venv
```
