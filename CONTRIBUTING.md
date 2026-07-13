# Contributing to Impact Engine

Thank you for your interest in contributing to Impact Engine. This guide covers setup, development workflow, and how to open a pull request.

For coding-agent and repository-specific implementation rules, see [`AGENTS.md`](AGENTS.md) and [`CLAUDE.md`](CLAUDE.md).

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Layout](#project-layout)
- [Git Workflow](#git-workflow)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Project Conventions](#project-conventions)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

- Read the [README](README.md) for product context.
- Check [open issues](https://github.com/Joey-1123/impact_engine/issues) before starting work.
- For security issues, follow [SECURITY.md](SECURITY.md) and do not file public issues.

## Development Setup

### 1. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | >= 3.8 | 3.10+ recommended |
| pip | Latest | Comes with Python |
| Git | Current stable | Required for cloning |
| Make | Optional | For convenience commands |

### 2. Clone and install

Fork the repository on GitHub first if you plan to submit changes, then clone your fork:

```bash
git clone git@github.com:YOUR_USERNAME/impact_engine.git
cd impact_engine
git remote add upstream git@github.com:Joey-1123/impact_engine.git
```

Create a virtual environment and install in development mode:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -e .
pip install rich fastapi uvicorn mcp lancedb openai anthropic google-genai
pip install pytest
```

### 3. Verify your setup

```bash
# Run the test suite
make test
# Or equivalently:
python -m unittest discover -s tests -p "test_*.py" -v
```

All 34 tests should pass.

### 4. Run tests and checks

| Goal | Command | Notes |
|---|---|---|
| Unit tests | `make test` | unittest discover over `tests/` |
| Single test file | `pytest tests/test_core.py -v` | pytest alternative |
| Build package | `make build` | Produces wheel + sdist |
| Clean artifacts | `make clean` | Removes build/ dist/ caches |

## Project Layout

```text
impact_engine/
├── cli/                     # Argparse entry point (25+ commands)
├── core/
│   ├── health/              # Scoring engine + 26 biomarker detectors
│   ├── graph/               # Knowledge graph construction
│   ├── parsers/             # Language-specific parsers
│   ├── providers/           # LLM + embedding providers
│   ├── persistence/         # Vector store
│   └── pipeline/            # Orchestrator
├── server/                  # FastAPI + MCP servers
├── web/                     # Next.js 15 dashboard
├── impact_web/              # Django web dashboard
├── tests/                   # Unit tests
├── AGENTS.md                # Coding-agent repo rules
├── CLAUDE.md                # Points to AGENTS.md
└── CONTRIBUTING.md          # This file
```

## Git Workflow

- Fork [Joey-1123/impact_engine](https://github.com/Joey-1123/impact_engine) and push branches to your fork.
- Pull requests target the `main` branch.
- Do not push directly to upstream unless explicitly authorized.

### Branch naming

Use a short descriptive branch name:

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

## Making Changes

1. Start from `main` and create a focused branch.
2. Keep the diff small and scoped to the issue you are solving.
3. Run tests locally before pushing.
4. Update docs with code whenever behavior, commands, or workflow changes.

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

## Submitting Changes

1. Push your branch to your fork.
2. Open a pull request against `Joey-1123/impact_engine:main`.
3. Link the issue using a closing keyword such as `Closes #42`.
4. Describe what changed and why.

## Project Conventions

- **No comments** unless explicitly asked.
- Use `pathlib.Path` over `os.path`.
- Use type hints on public functions.
- Keep functions focused and under ~200 lines.
- Follow existing patterns in neighboring files.
- Health scores are deterministic — no LLM calls in scoring logic.
- Never log secrets, API keys, or file contents.

Thank you for contributing to Impact Engine.
