# Impact Engine

<div align="center">
  <p><b>Static impact analysis for codebases — know your blast radius before you ship.</b></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
  [![Tests](https://img.shields.io/badge/tests-34%20passing-brightgreen)](tests/)
  [![Code of Conduct](https://img.shields.io/badge/Code%20of%20Conduct-Contributor%20Covenant-blueviolet)](CODE_OF_CONDUCT.md)
</div>

---

## What is Impact Engine?

Impact Engine is a **static impact analysis tool** that parses your codebase, builds a directed dependency graph of every function, detects changed functions via Git, and calculates exactly what will break. It runs purely on **static analysis** (Python AST) — no runtime execution, safe for any codebase.

---

## Key Features

- **Dependency Graphing** — Full call-graph extraction at function granularity
- **Impact Analysis** — `impact-engine impact <func>` shows every affected downstream
- **What-If Analysis** — `impact-engine predict <func>` simulates changes without touching git
- **Pre-Commit Hook** — `impact-engine pre-commit` blocks commits with risk above threshold
- **Weighted Risk Scoring** — Blast-radius risk per function weighted by cyclomatic complexity
- **Dead Code Detection** — Finds functions unreachable from entry points
- **Circular Dependency Detection** — `impact-engine cycles` finds import/function cycles
- **Cyclomatic Complexity** — `impact-engine complexity` ranks functions by McCabe score
- **Test Impact Mapping** — `impact-engine impact <func> --test-only` shows only affected tests
- **Decorator Tracking** — `@app.route(...)` and similar decorators tracked as deps
- **Multi-Language Support** — Plugin architecture with parsers for Python, JS/TS, Rust, Go, Java
- **HTML Export** — `impact-engine html` generates interactive D3.js dependency graph
- **Mermaid Export** — `impact-engine mermaid` generates editable Mermaid.js diagrams
- **SARIF Export** — `impact-engine sarif` outputs GitHub-code-scanning-compatible JSON
- **Compare Mode** — `impact-engine compare --base main` shows risk delta between branches
- **Watch Mode** — `impact-engine watch` / `impact-engine iwatch` continuously re-analyzes on file changes (watchdog or polling)
- **CI/CD Ready** — Structured JSON output (`--json`) for GitHub Actions bots
- **Web Dashboard** — Optional Django REST API with interactive graph, API key auth, and graph caching
- **Config File** — `.impactrc` (JSON) or `impact-engine.toml` for project-wide settings
- **SHA-256 Content Cache** — Incremental content-hash cache survives `git checkout`
- **.gitignore Aware** — Respects your existing `.gitignore` patterns

---

## Installation

```bash
git clone https://github.com/Joey-1123/impact_engine.git
cd impact-engine

python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows

pip install .
```

**Optional extras:**
```bash
pip install .[terminal]  # Rich terminal output (recommended)
pip install .[web]       # Django web dashboard
pip install .[visual]    # Graphviz PNG export
pip install .[watch]     # watchdog event-driven file watching
pip install .[full]      # All extras
```

---

## Usage

### Analyze everything
```bash
impact-engine analyze
```

### Summary with blast-radius ranking
```bash
impact-engine summary
impact-engine summary --json   # CI-ready JSON
```

### Specific function impact
```bash
impact-engine impact <function_name>
impact-engine impact <func> --test-only   # only affected tests
```

### What-if analysis (no git needed)
```bash
impact-engine predict <function_name>
impact-engine predict <func> --json
```

### Pre-commit check
```bash
impact-engine pre-commit
impact-engine pre-commit --threshold 3
```

### Current Git diff
```bash
impact-engine diff --json
```

### Complexity report
```bash
impact-engine complexity --limit 10
```

### Circular dependencies
```bash
impact-engine cycles
```

### Export graph
```bash
impact-engine mermaid > graph.md
impact-engine sarif > results.sarif
impact-engine html > report.html
```

### Compare branches
```bash
impact-engine compare --base main
```

### Watch for changes
```bash
impact-engine watch          # full re-analysis
impact-engine iwatch         # incremental (faster for large codebases)
```

### Compact controls
```bash
impact-engine graph --depth 3 --children 12 --changed-only
```

### Point at another repo
```bash
impact-engine summary --project /path/to/other/repo
```

### Install git hooks
```bash
make install-hooks
# or: sh scripts/install-hooks.sh
```

---

## Configuration

Create `.impactrc` or `impact-engine.toml` in your project root:

**JSON (`.impactrc`):**
```json
{
  "impact-engine": {
    "max_depth": 4,
    "max_children": 10,
    "limit": 20,
    "use_cache": true,
    "respect_gitignore": true,
    "risk_threshold_high": 10
  }
}
```

**TOML (`impact-engine.toml`):**
```toml
[impact-engine]
max_depth = 4
max_children = 10
limit = 20
use_cache = true
respect_gitignore = true
```

---

## Project Structure

```
impact_engine/
├── cli/main.py              # CLI entry point (17 commands, argparse)
├── core/
│   ├── extractor.py         # AST dependency extraction + line numbers + complexity
│   ├── graph_builder.py     # NetworkX directed graph
│   ├── traversal.py         # BFS impact propagation
│   ├── analyzer.py          # Risk scoring + dead code
│   ├── explainer.py         # Impact explanation with severity
│   ├── summary.py           # Ranked summaries + JSON payload
│   ├── git_analyzer.py      # Git diff → changed functions
│   ├── file_loader.py       # Python file scanning + .gitignore
│   ├── path_resolver.py     # Module name → file path resolution
│   ├── visualizer.py        # Rich terminal trees + complexity tables
│   ├── detector.py          # Cycle detection + entry point discovery
│   ├── exporter.py          # Mermaid + SARIF export
│   ├── html_exporter.py     # Interactive D3.js HTML report
│   ├── cache.py             # SHA-256 content-hash cache
│   ├── config.py            # .impactrc / impact-engine.toml loader
│   ├── comparator.py        # git merge-base branch comparison
│   ├── watcher.py           # file-change watcher (watchdog + polling fallback)
│   ├── js_extractor.py      # JS/TS dependency extraction
│   └── parsers/             # Multi-language parser plugin system
│       ├── __init__.py      # BaseParser, @register_parser, auto-discovery
│       ├── python_parser.py # Python (AST)
│       ├── js_parser.py     # JavaScript/TypeScript (regex)
│       ├── rust_parser.py   # Rust stub (tree-sitter)
│       ├── go_parser.py     # Go stub (tree-sitter)
│       └── java_parser.py   # Java stub (tree-sitter)
├── impact_web/              # Optional Django web dashboard
├── tests/                   # 34 tests across 22 test classes (+ __init__.py)
├── scripts/
│   ├── git-hooks/pre-commit # Pre-commit hook script
│   └── install-hooks.sh     # Hook installer
├── Makefile                 # install-hooks, test, build, clean
├── .pre-commit-config.yaml  # Pre-commit framework config
├── .github/workflows/
│   ├── impact.yml           # CI: analysis, comment, auto-label
│   └── branch-naming.yml    # Branch naming convention enforcement
└── setup.py                 # Package config
```

---

## How It Works

1. **Parse** — Reads files via AST (Python) or plugin parser (JS, Rust, Go, Java)
2. **Extract** — Walks AST to find function defs, calls, imports, decorators
3. **Build** — Constructs a `networkx.DiGraph` with caller→callee edges
4. **Detect** — `git status --porcelain` → changed files → changed functions
5. **Propagate** — BFS on reversed graph finds all impacted callers
6. **Score** — `risk = impact_count + max(0, complexity - 1)` — count + complexity bonus
7. **Output** — Terminal (Rich), JSON, Mermaid, SARIF, HTML (D3.js)

---

## Branch Naming Convention

The project follows an `impact/<type>-<description>` convention for feature/fix branches. The CI enforces:

| Pattern | Purpose |
|---------|---------|
| `main` / `master` | Stable releases |
| `feature/impact-<desc>` or `feat/impact-<desc>` | New features |
| `fix/impact-<desc>` or `bugfix/impact-<desc>` | Bug fixes |
| `chore/<desc>` | Maintenance |
| `refactor/<desc>` | Code refactoring |
| `docs/<desc>` | Documentation |
| `test/<desc>` | Testing |
| `ci/<desc>` | CI/CD changes |

---

## Web Dashboard (Optional)

```bash
pip install .[web]
cd impact_web
python manage.py migrate
python manage.py runserver
```

Set environment variables:
- `DJANGO_SECRET_KEY` — Required. Generate with `python -c 'import secrets; print(secrets.token_urlsafe(50))'`
- `DJANGO_DEBUG` — Set to `1` for development (defaults to `0`/off in production)
- `GITHUB_TOKEN` — GitHub PAT for PR commenting
- `GITHUB_WEBHOOK_SECRET` — Secret for webhook HMAC verification
- `ANALYZER_API_KEYS` — Comma-separated API keys for endpoint auth
- `DJANGO_ALLOWED_HOSTS` — Comma-separated allowed hosts

API endpoints:
- `GET /api/analyze/` — Full analysis (requires API key if configured)
- `GET /api/impact/?function=<name>` — Function impact (requires API key)
- `POST /webhook/github/` — GitHub webhook receiver (HMAC-verified)

---

## Development

```bash
# Run tests
python -m unittest discover -s tests -p "test_*.py" -v

# Build package
python -m build

# Install git hooks
make install-hooks
```

---

## Changelog

### v0.6.0
- **argparse CLI** — Migrated from hand-rolled flag parsing to `argparse` subparsers
- **Weighted risk** — Risk score = impact count + cyclomatic complexity bonus
- **SHA-256 cache** — Content-hash keys survive `git checkout` (no more stale mtime)
- **watchdog watcher** — Event-driven file watching with polling fallback
- **Unified git API** — Shared `run_git()`, `get_current_branch()`, `get_merge_base()`
- **XSS sanitization** — HTML export escapes node IDs via `html.escape()`
- **Actual SARIF line numbers** — `export_sarif()` now passes `linenos` dict for real line numbers
- **`rich` moved to extras** — `pip install .[terminal]` (graceful fallback to plain text)
- **`requests` moved to extras** — Only needed for GitHub bot; `pip install .[web]`
- **Stub parser warnings** — Go/Rust/Java parsers emit stderr warnings when invoked
- **Chained call fix** — `a.b.c()` now fully resolves (was truncated to `c`)
- **IfExp complexity** — Ternary expressions counted in cyclomatic complexity
- **Missing stdlib modules** — Added 25 missing stdlib modules to hardcoded set
- **`shlex.quote()`** — Git ref parameters quoted for injection safety
- **Code of Conduct** — Contributor Covenant added
- **Security policy** — SECURITY.md with reporting guidelines
- **`tests/__init__.py`** — Proper test packaging
- **34 tests** — all passing

### v0.5.0
- **4 new CLI commands** — `pre-commit`, `predict`, `html`, `iwatch`
- **`--test-only` flag** on `impact` command — filters results to test files
- **Pre-commit hook** — `impact-engine pre-commit` blocks commits above risk threshold
- **What-if analysis** — `impact-engine predict <func>` simulates changes without git
- **HTML export** — Interactive D3.js force-directed graph with risk coloring
- **Incremental watch** — `impact-engine iwatch` only re-analyzes changed files
- **Multi-language parser plugin architecture** — `core/parsers/` with auto-discovery
- **Plugin parsers** — Python (AST), JS/TS (regex), Rust/Go/Java (stubs for tree-sitter)
- **Web dashboard** — Graph caching (60s TTL), API key auth (`ANALYZER_API_KEYS`), HMAC webhook
- **CI improvements** — concurrency, cancel-in-progress, merge queue mode, auto-labeling, live-updating PR comments
- **Branch naming enforcement** — `.github/workflows/branch-naming.yml`
- **Git hooks** — `scripts/install-hooks.sh` + `make install-hooks`
- **VS Code extension stub** — commands for analyze, dependency tree, risk overview
- **34 tests** — all passing

### v0.4.0
- **12 CLI commands** — analyze, graph, summary, impact, diff, complexity, mermaid, sarif, compare, cycles, watch, version
- **Line number tracking** — every function node includes its source line
- **Cyclomatic complexity** — McCabe complexity per function with `impact-engine complexity`
- **Circular dependency detection** — `impact-engine cycles` finds function cycles
- **Decorator analysis** — decorator calls tracked as function dependencies
- **Mermaid export** — `impact-engine mermaid` for editable diagrams
- **SARIF export** — GitHub code scanning compatible JSON
- **Compare mode** — `impact-engine compare --base main` shows risk deltas between branches
- **Watch mode** — `impact-engine watch` re-analyzes on file changes
- **Config file** — `.impactrc` (JSON) and `impact-engine.toml` support
- **AST cache** — mtime-based `.impact_cache` skips unchanged files
- **.gitignore awareness** — file loader respects `.gitignore` patterns
- **JS/TS extraction** — basic dependency extraction for JavaScript/TypeScript
- **Relative import support** — `from .module import func` now resolves correctly
- **Package resolution** — `pkg/__init__.py` resolved when `pkg.py` doesn't exist
- **Stdlib filtering** — comprehensive stdlib module blacklist prevents noise
- **Self/class method calls** — `self.method()` and `cls.method()` tracked
- **Bug fixes** — explainer shortest path direction, GitHub Actions field names, Django SECRET_KEY enforcement
- **34 tests** across 22 test classes (up from 5 tests)
- **Type hints** across all core modules

### v0.3.0
- CLI surface with `--version`
- `summary --json` for CI/PR bots
- Split packaging (core, web, visual)
- Terminal summary view and graph controls
- Extractor normalization, Git detection, summary tests

---

## License

MIT License — see [LICENSE](LICENSE).

---

**Built by Shubham Panchal (Joey)**
