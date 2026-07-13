# Changelog

## v0.7.0
- **Health Scoring Engine** — 3D health score (defect, maintainability, performance) with 26 biomarker detectors across structural, performance, and organizational dimensions
- **Knowledge Graph** — PageRank centrality, community detection (greedy modularity), layer inference, entry-point tours
- **Duplication Detection** — Rabin-Karp rolling hash clone detection with per-file duplication percentage
- **Decision Mining** — Extract design decisions from git log, ADR files, and changelogs
- **Cost Estimator** — Heuristic token costing per page type across 7 LLM models
- **FastAPI Server** — 7 routers (health, overview, graph, health-score, costs, decisions, workspace) with cached async analysis
- **Web UI** — Next.js 15 App Router with 4 pages (dashboard, overview, graph, decisions)
- **MCP Server** — FastMCP with 4 tools (get_overview, get_health, get_graph, list_tools)
- **LLM Providers** — OpenAI, Anthropic, Gemini async providers with embedder and extensible registry
- **Vector Store** — ABC with InMemory and LanceDB backends, cosine similarity search
- **CLI** — 7 new commands: health, kg, decisions, cost, duplication, serve, mcp; all with `--json` output
- **Refactoring Detectors** — Extract class, extract method, break cycle, move method, split file
- **Blame Index** — Function-level git blame with code age, churn, and ownership signals
- **Dead Code Confidence** — Risk-factor scoring for dead-code deletion safety
- **PR Blast Radius** — Extend traversal with risk-scored impact propagation
- **Contributor Profiles** — Ownership risk, developer congestion, knowledge loss detection

## v0.6.0
- **argparse CLI** — Migrated from hand-rolled flag parsing to `argparse` subparsers with help for every command
- **Weighted risk model** — Risk score = impact count + `max(0, complexity - 1)` bonus
- **SHA-256 content cache** — Replaced mtime with content hashing; survives `git checkout`
- **watchdog watcher** — Event-driven file watching via `watchdog` with polling fallback
- **Unified git API** — `run_git()`, `get_current_branch()`, `get_merge_base()` shared across modules
- **XSS sanitization** — HTML export escapes node IDs via `html.escape()`
- **SARIF line numbers** — Actual function line numbers in SARIF instead of hardcoded `startLine: 1`
- **`rich` moved to extras** — `pip install impact-engine[terminal]` (graceful fallback to plain text)
- **`requests` moved to extras** — `pip install impact-engine[web]` (only used by GitHub bot)
- **Stub parser warnings** — Go/Rust/Java parsers print stderr warnings when invoked
- **Chained call fix** — `a.b.c()` fully resolves instead of truncating to `c`
- **IfExp complexity** — Ternary expressions counted in cyclomatic complexity
- **Missing stdlib modules** — 25 additional modules added to hardcoded stdlib set
- **`shlex.quote()`** — Git ref parameters quoted for shell injection safety
- **`tests/__init__.py`** — Proper test packaging
- **CODE_OF_CONDUCT.md** — Contributor Covenant
- **SECURITY.md** — Security vulnerability reporting guidelines
- **34 tests** — all passing

## v0.5.0
- 4 new CLI commands: `pre-commit`, `predict`, `html`, `iwatch`
- `--test-only` flag on `impact` command — filters results to test files
- Pre-commit hook — `impact-engine pre-commit` blocks commits above risk threshold
- What-if analysis — `impact-engine predict <func>` simulates changes without git
- HTML export — Interactive D3.js force-directed graph with risk coloring
- Incremental watch — `impact-engine iwatch` only re-analyzes changed files
- Multi-language parser plugin architecture with auto-discovery
- Plugin parsers: Python (AST), JS/TS (regex), Rust/Go/Java (stubs)
- Web dashboard with graph caching, API key auth, HMAC webhooks
- CI improvements: concurrency, cancel-in-progress, merge queue, auto-labeling
- Branch naming enforcement workflow
- Git hooks installer (`make install-hooks`)
- VS Code extension stub
- 34 tests — all passing

## v0.4.0
- 12 CLI commands: analyze, graph, summary, impact, diff, complexity, mermaid, sarif, compare, cycles, watch, version
- Line number tracking per function
- Cyclomatic complexity ranking
- Circular dependency detection
- Decorator analysis
- Mermaid and SARIF export
- Compare mode with `--base`
- Watch mode
- Config file support (`.impactrc` JSON, `impact-engine.toml`)
- AST cache (mtime-based)
- JS/TS extraction
- 34 tests across 22 test classes

## v0.3.0
- Versioned CLI surface with `impact-engine --version`
- `impact-engine summary --json` for CI and PR bots
- Split packaging into core, web, and visual extras
- Terminal-first summary view and cleaner graph controls
- Focused tests for extractor normalization, Git detection, and summary payloads
