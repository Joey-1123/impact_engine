#  Impact Analyzer

<div align="center">
  <p><b>Make developers understand impact before they break things.</b></p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
  [![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
</div>

---

##  What is Impact Analyzer?

Impact Analyzer is the current release of a static analysis tool designed to prevent regressions and unseen bugs. By analyzing your codebase, it tracks how functions depend on each other, detects changes via Git, and maps out exactly what will be affected by your latest commit.

The current release is terminal-first: use the CLI for summaries, changed-function analysis, and machine-readable JSON output.

---

##  Key Features

* ** Dependency Graphing:** Understand exactly how functions connect across your entire project.
* ** Impact Analysis:** Instantly see what breaks when you modify a specific function.
* ** Risk Scoring:** Every function gets a dynamic risk score based on how far its impact propagates.
* ** Smart Filtering:** Cut through the noise and focus only on relevant or high-risk architectural changes.
* ** Universal Access:** Run it in the terminal via CLI, or seamlessly directly inside your editor with the VS Code Extension.

---

##  Installation

**1. Clone the repository**
```bash
git clone https://github.com/your-username/impact-analyzer.git
cd impact-analyzer
```

**2. Create a virtual environment**
```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate   

# Windows
.venv\Scripts\activate      
```

**3. Install the CLI engine**
```bash
pip install .
```

**4. Optional web dashboard**
```bash
pip install .[web]
```

**5. Optional PNG export**
```bash
pip install .[visual]
```

---

##  Usage

###  CLI Engine

**🔹 Analyze the whole project**
```bash
impact-engine analyze
```

**Terminal graph**
```bash
impact-engine graph
```

**Summary view**
```bash
impact-engine summary
```

The summary ranks blast radius: functions with the most upstream dependents bubble to the top.

**JSON summary for bots**
```bash
impact-engine summary --json
```

**Compact graph controls**
```bash
impact-engine graph --depth 3 --children 12 --changed-only
```

**Version**
```bash
impact-engine --version
```

**🔹 Find the impact of a specific function**
```bash
impact-engine impact <function_name>

# Example:
impact-engine impact extract_dependencies
```

**🔹 Analyze current Git changes**
Outputs a structured JSON payload detailing max risk, affected files, and dependency edges.
```bash
impact-engine diff --json
```

### Testing

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Release Build

```bash
python -m build
```

##  Changelog

### v0.3.0
- Added a versioned CLI surface with `impact-engine --version`.
- Added `impact-engine summary --json` for CI and PR bots.
- Split packaging into core CLI, optional web, and optional visual extras.
- Added a terminal-first summary view and cleaner graph controls.
- Added focused tests for extractor normalization, Git detection, and summary payloads.

### Use on Another Repo

Install Impact Engine once, then point it at any repository path:

```bash
impact-engine summary --project D:\projects\learnalytics
impact-engine summary --json --project D:\projects\learnalytics
impact-engine graph --changed-only --project D:\projects\learnalytics
impact-engine diff --json --project D:\projects\learnalytics
```

If you want to update the package in a different virtual environment:

```bash
pip uninstall impact-engine -y
pip install -U F:\impact_engine
```

### Troubleshooting

If `impact-engine` still imports old code from another environment:

1. Confirm you are in the right venv.
2. Run `pip uninstall impact-engine -y`.
3. Reinstall from the local repo path with `pip install -U F:\impact_engine`.
4. Recheck the version with `impact-engine --version`.

If you see `ModuleNotFoundError: No module named 'graphviz'`:

1. The base CLI does not require Graphviz anymore.
2. Install the optional visual extras only if you need PNG export:

```bash
pip install -U "F:\impact_engine[visual]"
```

If a command says `path does not exist`, pass the target repo with `--project` or run the command from inside that repo.

### VS Code Extension

Optional later. The CLI is the primary product surface now.

---

##  How It Works

1.  **Parse:** Reads your code using Python's AST (Abstract Syntax Tree).
2.  **Extract:** Identifies function-level dependencies and calls.
3.  **Build:** Constructs a directed network graph of your architecture.
4.  **Detect:** Cross-references the graph with changed functions detected via Git.
5.  **Propagate:** Calculates how the impact travels through the graph.
6.  **Score:** Assigns a risk score to the changes.
7.  **Visualize:** Outputs structured JSON for the UI to render the interactive maps.

> ** Example Flow:** > `diff_command` ➔ `extract_project_dependencies` ➔ `get_python_files`
> *Change one function → see the full impact chain.*

---

##  Project Structure

```text
impact_engine/
│
├── cli/                 # CLI commands (entry point)
├── core/                # Core analysis logic
│   ├── extractor.py     # AST-based dependency extraction
│   ├── graph_builder.py # Builds dependency graph
│   ├── git_analyzer.py  # Detects changed functions
│   ├── analyzer.py      # Risk calculation
│   ├── file_loader.py   # File scanning
│   └── visualizer.py    # Graph rendering
│
├── impact_web/          # (Optional) API / web integration
├── tests/               # Test files
└── main.py              # CLI entry
```

---

##  Roadmap

- [ ]  **Interactive graph updates:** Highlight specific impact chains on hover.
- [ ] **AI Explanations:** Automated reasoning for *why* a risk score is high.
- [ ]  **CI/CD Integration:** Automated PR comment generation.
- [ ]  **Inline Diagnostics:** ESLint-style inline editor warnings for high-risk changes.
- [ ] **Web Dashboard:** A standalone portal for team-wide impact review.

---

## 🤝 Contributing & License

Pull requests are always welcome! If you have ideas for new features or find a bug, please open an issue.

This project is licensed under the **MIT License**.

---

**👨‍💻 Built by Shubham Panchal (Joey)**
