#  Impact Analyzer

<div align="center">
  <p><b>Make developers understand impact before they break things.</b></p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
  [![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
</div>

---

##  What is Impact Analyzer?

Impact Analyzer is a powerful static analysis tool designed to prevent regressions and unseen bugs. By analyzing your codebase, it tracks how functions depend on each other, detects changes via Git, and maps out exactly what will be affected by your latest commit. 

Whether you are in the terminal or your IDE, Impact Analyzer calculates risk scores and visualizes dependency graphs so you can code with confidence.

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

**3. Install the engine**
```bash
pip install -e .
```

---

##  Usage

###  CLI Engine

**🔹 Analyze the whole project**
```bash
impact-engine analyze
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

### VS Code Extension

Bring the power of the engine directly into your workflow. 

* **Run command:** `Impact Analyzer: Run Analysis`
* **Interactive Visual Graph:** Pan and zoom through your impact chain.
* **Click-to-Code:** Click any node in the graph to jump straight to that function in your editor.
* **Highlighting:** Visually highlights impacted code right in your text editor.

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

## 📌 Roadmap

- [ ]  **Interactive graph updates:** Highlight specific impact chains on hover.
- [ ] 🧠**AI Explanations:** Automated reasoning for *why* a risk score is high.
- [ ]  **CI/CD Integration:** Automated PR comment generation.
- [ ]  **Inline Diagnostics:** ESLint-style inline editor warnings for high-risk changes.
- [ ] **Web Dashboard:** A standalone portal for team-wide impact review.

---

## 🤝 Contributing & License

Pull requests are always welcome! If you have ideas for new features or find a bug, please open an issue.

This project is licensed under the **MIT License**.

---

**👨‍💻 Built by Shubham Panchal (Joey)**