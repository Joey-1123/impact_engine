# Impact Engine

<div align="center">
  <p><b>Static impact analysis for Python codebases — know your blast radius before you ship.</b></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
  [![Tests](https://img.shields.io/badge/tests-34%20passing-brightgreen)](tests/)
</div>

---

## What is Impact Engine?

Impact Engine is a **static impact analysis tool** that parses your Python codebase, builds a directed dependency graph of every function, detects changed functions via Git, and calculates exactly what will break. It runs purely on **static analysis** (Python's AST) — no runtime execution, safe for any codebase.

---

## Key Features

- **Dependency Graphing** — Full call-graph extraction at function granularity
- **Impact Analysis** — `impact-engine impact <func>` shows every affected downstream
- **Risk Scoring** — Blast-radius risk per function (number of impacted callers)
- **Dead Code Detection** — Finds functions unreachable from entry points
- **Circular Dependency Detection** — `impact-engine cycles` finds import/function cycles
- **Cyclomatic Complexity** — `impact-engine complexity` ranks functions by McCabe score
- **Decorator Tracking** — `@app.route(...)` and similar decorators tracked as deps
- **Line Number Tracking** — Every function node includes its source line
- **Smart Filtering** — Depth, children, and `--changed-only` flags for large repos
- **Mermaid Export** — `impact-engine mermaid` generates editable Mermaid.js diagrams
- **SARIF Export** — `impact-engine sarif` outputs GitHub-code-scanning-compatible JSON
- **Compare Mode** — `impact-engine compare --base main` shows risk delta between branches
- **Watch Mode** — `impact-engine watch` continuously re-analyzes on file changes
- **CI/CD Ready** — Structured JSON output (`--json`) for GitHub Actions bots
- **Web Dashboard** — Optional Django REST API + Cytoscape.js interactive graph
- **Config File** — `.impactrc` (JSON) or `impact-engine.toml` for project-wide settings
- **AST Cache** — Incremental mtime-based cache skips unchanged files
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
pip install .[web]     # Django web dashboard
pip install .[visual]  # Graphviz PNG export
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
```

### Compare branches
```bash
impact-engine compare --base main
```

### Watch for changes
```bash
impact-engine watch
```

### Compact controls
```bash
impact-engine graph --depth 3 --children 12 --changed-only
```

### Point at another repo
```bash
impact-engine summary --project /path/to/other/repo
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
├── cli/main.py          # CLI entry point (12 commands)
├── core/
│   ├── extractor.py     # AST dependency extraction + line numbers + complexity
│   ├── graph_builder.py # NetworkX directed graph
│   ├── traversal.py     # BFS impact propagation
│   ├── analyzer.py      # Risk scoring + dead code
│   ├── explainer.py     # Impact explanation with severity
│   ├── summary.py       # Ranked summaries + JSON payload
│   ├── git_analyzer.py  # Git diff → changed functions
│   ├── file_loader.py   # Python file scanning + .gitignore
│   ├── path_resolver.py # Module name → file path resolution
│   ├── visualizer.py    # Rich terminal trees + complexity tables
│   ├── detector.py      # Cycle detection + entry point discovery
│   ├── exporter.py      # Mermaid + SARIF export
│   ├── cache.py         # mtime-based AST cache
│   ├── config.py        # .impactrc / impact-engine.toml loader
│   ├── comparator.py    # git merge-base branch comparison
│   ├── watcher.py       # file-change polling watcher
│   └── js_extractor.py  # JS/TS dependency extraction
├── impact_web/          # Optional Django web dashboard
├── tests/               # 34 tests across 22 test classes
└── setup.py             # Package config
```

---

## How It Works

1. **Parse** — Reads Python files via `ast.parse`
2. **Extract** — Walks AST to find function defs, calls, imports, decorators
3. **Build** — Constructs a `networkx.DiGraph` with caller→callee edges
4. **Detect** — `git status --porcelain` → changed files → changed functions
5. **Propagate** — BFS on reversed graph finds all impacted callers
6. **Score** — `risk = len(get_impact(func))` — count of transitive callers
7. **Output** — Terminal (Rich), JSON, Mermaid, SARIF

---

## Development

```bash
# Run tests
python -m unittest discover -s tests -p "test_*.py" -v

# Build package
python -m build
```

---

## Changelog

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
