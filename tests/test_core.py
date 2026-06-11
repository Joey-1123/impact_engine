# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from core.extractor import extract_project_dependencies
from core.git_analyzer import get_changed_files, get_changed_functions
from core.summary import build_analysis_summary, build_analysis_summary_payload
from core.version import __version__


class ExtractorTests(unittest.TestCase):
    def test_imported_functions_normalize_to_project_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pkg").mkdir()
            (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
            (root / "pkg" / "util.py").write_text(
                "def helper():\n    return 1\n",
                encoding="utf-8",
            )
            (root / "pkg" / "main.py").write_text(
                "from pkg.util import helper\n\n"
                "def run():\n"
                "    return helper()\n",
                encoding="utf-8",
            )

            deps = extract_project_dependencies(str(root))

            self.assertIn("pkg/main.py::run", deps)
            self.assertIn("pkg/util.py::helper", deps["pkg/main.py::run"])


class GitAnalyzerTests(unittest.TestCase):
    def test_worktree_mode_detects_staged_and_untracked_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "config", "user.email", "tester@example.com"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Tester"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            tracked = root / "tracked.py"
            staged = root / "staged.py"
            untracked = root / "untracked.py"

            tracked.write_text("def alpha():\n    return 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.py"], cwd=root, check=True, capture_output=True, text=True)

            staged.write_text("def beta():\n    return 2\n", encoding="utf-8")
            subprocess.run(["git", "add", "staged.py"], cwd=root, check=True, capture_output=True, text=True)

            untracked.write_text("def gamma():\n    return 3\n", encoding="utf-8")

            deps = {
                "tracked.py::alpha": [],
                "staged.py::beta": [],
            }

            files = get_changed_files(cwd=str(root))
            self.assertIn("tracked.py", files)
            self.assertIn("staged.py", files)
            self.assertIn("untracked.py", files)

            changed_funcs = get_changed_functions(deps, cwd=str(root))
            self.assertIn("tracked.py::alpha", changed_funcs)
            self.assertIn("staged.py::beta", changed_funcs)


class BaseDummyGraph:
    def has_node(self, node):
        return node in self.nodes()


class SummaryTests(unittest.TestCase):
    def test_summary_ranks_high_risk_nodes_first(self):
        class DummyGraph(BaseDummyGraph):
            def __init__(self):
                self._nodes = ["a.py::a", "a.py::b", "a.py::c", "a.py::d", "x.py::x", "x.py::y"]
                self._edges = {
                    "a.py::a": {"a.py::b", "a.py::c"},
                    "a.py::b": {"a.py::d"},
                    "a.py::c": set(),
                    "a.py::d": set(),
                    "x.py::x": {"x.py::y"},
                    "x.py::y": set(),
                }

            def nodes(self):
                return list(self._nodes)

            def number_of_nodes(self):
                return len(self._nodes)

            def number_of_edges(self):
                return sum(len(v) for v in self._edges.values())

            def out_degree(self, node):
                return len(self._edges.get(node, set()))

            def in_degree(self, node):
                return sum(1 for edges in self._edges.values() if node in edges)

            def reverse(self):
                rev = {node: set() for node in self._nodes}
                for source, targets in self._edges.items():
                    for target in targets:
                        rev[target].add(source)

                class ReversedGraph:
                    def __init__(self, adjacency):
                        self._adjacency = adjacency

                    def neighbors(self, node):
                        return list(self._adjacency.get(node, set()))

                return ReversedGraph(rev)

        graph = DummyGraph()
        summary = build_analysis_summary(graph, changed_nodes=["a.py::a", "x.py::x"], dead_nodes=["z.py::z"])

        self.assertEqual(summary["counts"]["nodes"], 6)
        self.assertEqual(summary["counts"]["dead"], 1)
        self.assertEqual(summary["top_hotspots"][0]["risk"], 2)
        self.assertTrue(summary["changed_hotspots"])

    def test_json_summary_payload_is_machine_friendly(self):
        class DummyGraph(BaseDummyGraph):
            def nodes(self):
                return ["a.py::a", "a.py::b"]

            def number_of_nodes(self):
                return 2

            def number_of_edges(self):
                return 1

            def out_degree(self, node):
                return 1 if node == "a.py::a" else 0

            def in_degree(self, node):
                return 0 if node == "a.py::a" else 1

            def reverse(self):
                class ReversedGraph:
                    def neighbors(self, node):
                        return ["a.py::a"] if node == "a.py::b" else []

                return ReversedGraph()

        payload = build_analysis_summary_payload(
            DummyGraph(),
            changed_nodes=["a.py::a"],
            dead_nodes=["a.py::b"],
            limit=5,
        )

        self.assertIn("counts", payload)
        self.assertIn("version", payload)
        self.assertIn("top_hotspots", payload)
        self.assertIn("dead_nodes", payload)
        self.assertEqual(payload["counts"]["nodes"], 2)
        self.assertEqual(payload["dead_nodes"], ["a.py::b"])
        self.assertRegex(payload["version"], r"^\d+\.\d+\.\d+")


class VersionTests(unittest.TestCase):
    def test_version_string_exists(self):
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+")



class DeadCodeTests(unittest.TestCase):
    def test_find_dead_code_detects_unreachable_functions(self):
        from core.analyzer import find_dead_code
        import networkx as nx

        g = nx.DiGraph()
        g.add_edge("a.py::main", "a.py::used")
        g.add_edge("a.py::main", "a.py::also_used")
        g.add_node("a.py::unused")

        dead = find_dead_code(g, ["a.py::main"])
        self.assertIn("a.py::unused", dead)
        self.assertNotIn("a.py::used", dead)
        self.assertNotIn("a.py::main", dead)

    def test_find_dead_code_returns_empty_when_all_reachable(self):
        from core.analyzer import find_dead_code
        import networkx as nx

        g = nx.DiGraph()
        g.add_edge("app.py::main", "app.py::helper")
        g.add_edge("app.py::helper", "app.py::util")

        dead = find_dead_code(g, ["app.py::main"])
        self.assertEqual(dead, [])


class ExplainerTests(unittest.TestCase):
    def test_explain_impact_lists_direct_dependents(self):
        from core.explainer import explain_impact
        import networkx as nx

        g = nx.DiGraph()
        g.add_edge("a.py::caller", "a.py::target")
        impacted = {"a.py::caller"}
        result = explain_impact(g, "a.py::target", impacted)

        self.assertEqual(result["severity"], "LOW")
        self.assertEqual(len(result["details"]), 1)
        self.assertIn("directly depends", result["details"][0]["reason"])

    def test_explain_impact_lists_indirect_dependents(self):
        from core.explainer import explain_impact
        import networkx as nx

        g = nx.DiGraph()
        g.add_edge("a.py::caller", "a.py::middle")
        g.add_edge("a.py::middle", "a.py::target")
        impacted = {"a.py::caller", "a.py::middle"}
        result = explain_impact(g, "a.py::target", impacted)

        reasons = [e["reason"] for e in result["details"]]
        self.assertTrue(any("directly depends" in r for r in reasons))
        self.assertTrue(any("via" in r for r in reasons))

    def test_explain_impact_high_severity_for_large_impact(self):
        from core.explainer import explain_impact
        import networkx as nx

        g = nx.DiGraph()
        g.add_node("a.py::target")
        impacted = set()
        for i in range(5):
            caller = f"a.py::caller_{i}"
            g.add_edge(caller, "a.py::target")
            impacted.add(caller)

        result = explain_impact(g, "a.py::target", impacted)
        self.assertEqual(result["severity"], "HIGH")

    def test_explain_impact_skips_self_loop(self):
        from core.explainer import explain_impact
        import networkx as nx

        g = nx.DiGraph()
        g.add_node("a.py::func")

        result = explain_impact(g, "a.py::func", {"a.py::func"})
        self.assertEqual(len(result["details"]), 0)


class EntryPointTests(unittest.TestCase):
    def test_extract_project_entry_points_finds_main_block(self):
        import tempfile
        from pathlib import Path
        from core.extractor import extract_project_entry_points

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "run.py").write_text(
                "def main():\n    pass\n\n"
                "if __name__ == '__main__':\n    main()\n",
                encoding="utf-8",
            )

            entry_points = extract_project_entry_points(str(root))
            self.assertIn("run.py::main", entry_points)


class ExtractFeaturesTests(unittest.TestCase):
    def test_relative_import_resolution(self):
        import tempfile
        from pathlib import Path
        from core.extractor import extract_project_dependencies

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "pkg"
            pkg.mkdir()
            (pkg / "__init__.py").write_text("from .sub import helper\n", encoding="utf-8")
            (pkg / "sub.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
            (pkg / "main.py").write_text(
                "from .sub import helper\n\n"
                "def run():\n    return helper()\n",
                encoding="utf-8",
            )

            deps = extract_project_dependencies(str(root))
            self.assertIn("pkg/main.py::run", deps)

    def test_package_init_py_resolution(self):
        import tempfile
        from pathlib import Path
        from core.extractor import extract_project_dependencies

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "mypackage"
            pkg.mkdir()
            (pkg / "__init__.py").write_text(
                "def setup():\n    return 0\n",
                encoding="utf-8",
            )
            (pkg / "app.py").write_text(
                "from mypackage import setup\n\n"
                "def start():\n    return setup()\n",
                encoding="utf-8",
            )

            deps = extract_project_dependencies(str(root))
            self.assertIn("mypackage/app.py::start", deps)

    def test_star_import_does_not_crash(self):
        import tempfile
        from pathlib import Path
        from core.extractor import extract_project_dependencies

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mod.py").write_text(
                "from os.path import *\n\ndef run():\n    return join('a', 'b')\n",
                encoding="utf-8",
            )

            deps = extract_project_dependencies(str(root))
            self.assertIn("mod.py::run", deps)

    def test_extractor_skips_stdlib_imports(self):
        import tempfile
        from pathlib import Path
        from core.extractor import extract_project_dependencies

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text(
                "import os\nimport json\n\ndef run():\n    return os.getcwd()\n",
                encoding="utf-8",
            )

            deps = extract_project_dependencies(str(root))
            self.assertIn("app.py::run", deps)


class RiskCalculationTests(unittest.TestCase):
    def test_calculate_risk_counts_impacted_nodes(self):
        from core.analyzer import calculate_risk
        import networkx as nx

        g = nx.DiGraph()
        g.add_edge("a.py::a", "a.py::b")
        g.add_edge("a.py::b", "a.py::c")

        risk = calculate_risk(g, "a.py::c")
        self.assertEqual(risk, 2)

        risk = calculate_risk(g, "a.py::b")
        self.assertEqual(risk, 1)

        risk = calculate_risk(g, "a.py::a")
        self.assertEqual(risk, 0)

    def test_calculate_risk_returns_zero_for_unknown_node(self):
        from core.analyzer import calculate_risk
        import networkx as nx

        g = nx.DiGraph()
        risk = calculate_risk(g, "nonexistent")
        self.assertEqual(risk, 0)


class CycleDetectionTests(unittest.TestCase):
    def test_find_cycles_detects_simple_cycle(self):
        from core.detector import find_cycles
        import networkx as nx

        g = nx.DiGraph()
        g.add_edge("a.py::a", "a.py::b")
        g.add_edge("a.py::b", "a.py::a")

        cycles = find_cycles(g)
        self.assertTrue(len(cycles) > 0)
        self.assertTrue(any("a.py::a" in c for c in cycles))

    def test_find_cycles_returns_empty_for_acyclic(self):
        from core.detector import find_cycles
        import networkx as nx

        g = nx.DiGraph()
        g.add_edge("a.py::a", "a.py::b")
        g.add_edge("a.py::b", "a.py::c")

        cycles = find_cycles(g)
        self.assertEqual(cycles, [])


class FileLoaderTests(unittest.TestCase):
    def test_get_python_files_skips_ignored_dirs(self):
        from core.file_loader import get_python_files
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".venv").mkdir()
            (root / ".venv" / "lib.py").write_text("x=1\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("def f(): pass\n", encoding="utf-8")

            files = get_python_files(str(root))
            paths = [str(Path(f).relative_to(root)) for f in files]
            self.assertIn("src/main.py", paths)
            self.assertNotIn(".venv/lib.py", paths)

    def test_get_python_files_respects_gitignore(self):
        from core.file_loader import get_python_files, pathspec
        import tempfile
        from pathlib import Path

        if pathspec is None:
            self.skipTest("pathspec not installed")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("generated/\n", encoding="utf-8")
            (root / "generated").mkdir()
            (root / "generated" / "code.py").write_text("x=1\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("def f(): pass\n", encoding="utf-8")

            files = get_python_files(str(root), respect_gitignore=True)
            paths = [str(Path(f).relative_to(root)) for f in files]
            self.assertIn("src/main.py", paths)
            self.assertNotIn("generated/code.py", paths)



class LineNumberTests(unittest.TestCase):
    def test_function_linenos_are_extracted(self):
        import tempfile
        from pathlib import Path
        from core.extractor import extract_dependencies

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mod.py").write_text(
                "def foo():\n    pass\n\ndef bar():\n    return 1\n",
                encoding="utf-8",
            )

            deps, entry_funcs, linenos, complexities = extract_dependencies(
                str(root / "mod.py"), str(root)
            )
            self.assertIn("mod.py::foo", linenos)
            self.assertEqual(linenos["mod.py::foo"], 1)
            self.assertIn("mod.py::bar", linenos)
            self.assertEqual(linenos["mod.py::bar"], 4)


class ComplexityTests(unittest.TestCase):
    def test_cyclomatic_complexity_is_computed(self):
        import tempfile
        from pathlib import Path
        from core.extractor import extract_dependencies

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mod.py").write_text(
                "def simple():\n    return 1\n\n"
                "def complex():\n"
                "    if a:\n        pass\n"
                "    for x in y:\n        pass\n"
                "    while z:\n        pass\n",
                encoding="utf-8",
            )

            deps, entry_funcs, linenos, complexities = extract_dependencies(
                str(root / "mod.py"), str(root)
            )
            self.assertEqual(complexities.get("mod.py::simple"), 1)
            self.assertGreaterEqual(complexities.get("mod.py::complex", 0), 4)


class DecoratorTests(unittest.TestCase):
    def test_decorator_calls_are_tracked(self):
        import tempfile
        from pathlib import Path
        from core.extractor import extract_dependencies

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "deco.py").write_text(
                "def logger(f):\n    return f\n\n"
                "@logger\ndef greet():\n    return 'hi'\n",
                encoding="utf-8",
            )

            deps_as_tuples, _, _, _ = extract_dependencies(
                str(root / "deco.py"), str(root)
            )
            greet_func = [k for k in deps_as_tuples if k.endswith("::greet")]
            self.assertTrue(len(greet_func) >= 1)
            if greet_func:
                self.assertIn("deco.py::logger", deps_as_tuples.get(greet_func[0], []))


class CacheTests(unittest.TestCase):
    def test_cache_layer_stores_and_retrieves(self):
        import tempfile
        from pathlib import Path
        import time
        from core.cache import extract_project_dependencies_cached

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mod.py").write_text("def f():\n    return 1\n", encoding="utf-8")

            deps1, linenos1, comp1 = extract_project_dependencies_cached(
                str(root), use_cache=True
            )

            (root / ".impact_cache").exists()

            deps2, linenos2, comp2 = extract_project_dependencies_cached(
                str(root), use_cache=True
            )

            self.assertEqual(deps1, deps2)


class ConfigTests(unittest.TestCase):
    def test_load_config_from_json(self):
        import tempfile
        from pathlib import Path
        from core.config import load_config

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".impactrc").write_text(
                '{"impact-engine": {"max_depth": 5, "limit": 20}}',
                encoding="utf-8",
            )

            config = load_config(str(root))
            self.assertEqual(config.get("max_depth"), 5)
            self.assertEqual(config.get("limit"), 20)

    def test_load_config_from_toml(self):
        import tempfile
        from pathlib import Path
        from core.config import load_config

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "impact-engine.toml").write_text(
                '[impact-engine]\nmax_depth = 4\nlimit = 15\n',
                encoding="utf-8",
            )

            config = load_config(str(root))
            self.assertEqual(config.get("max_depth"), 4)
            self.assertEqual(config.get("limit"), 15)

    def test_merge_config_prefers_cli_over_file(self):
        from core.config import merge_config

        config = {"max_depth": 3, "limit": 10}
        cli = {"max_depth": 5, "limit": None}
        merged = merge_config(cli, config)
        self.assertEqual(merged["max_depth"], 5)
        self.assertEqual(merged["limit"], 10)


class JsExtractorTests(unittest.TestCase):
    def test_extract_js_functions(self):
        import tempfile
        from pathlib import Path
        from core.js_extractor import extract_js_dependencies

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.js").write_text(
                "function greet() {\n  return 'hello';\n}\n\n"
                "function main() {\n  greet();\n}\n",
                encoding="utf-8",
            )

            deps = extract_js_dependencies(str(root / "app.js"), str(root))
            self.assertIn("app.js::main", deps)
            self.assertIn("app.js::greet", deps)

    def test_extract_js_imports(self):
        import tempfile
        from pathlib import Path
        from core.js_extractor import extract_js_dependencies

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sub = root / "lib"
            sub.mkdir()
            (sub / "helper.js").write_text("function help() { return 1; }\n", encoding="utf-8")
            (root / "app.js").write_text(
                "const { help } = require('./lib/helper');\n"
                "function run() {\n  help();\n}\n",
                encoding="utf-8",
            )

            deps = extract_js_dependencies(str(root / "app.js"), str(root))
            self.assertIn("app.js::run", deps)


class MermaidExportTests(unittest.TestCase):
    def test_export_mermaid_creates_valid_output(self):
        import networkx as nx
        from core.exporter import export_mermaid

        g = nx.DiGraph()
        g.add_edge("a.py::foo", "a.py::bar")

        output = export_mermaid(g)
        self.assertIn("graph TD", output)
        self.assertIn("foo", output)
        self.assertIn("bar", output)


class SarifExportTests(unittest.TestCase):
    def test_export_sarif_creates_valid_output(self):
        import networkx as nx
        from core.exporter import export_sarif
        import json

        g = nx.DiGraph()
        g.add_edge("a.py::foo", "a.py::bar")

        output = export_sarif(g, changed_nodes=["a.py::foo"])
        sarif = json.loads(output)
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertEqual(len(sarif["runs"]), 1)
        self.assertIn("results", sarif["runs"][0])


class ComparatorTests(unittest.TestCase):
    def test_compare_branches_returns_structure(self):
        import tempfile
        from pathlib import Path
        import subprocess
        from core.comparator import compare_branches

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            subprocess.run(["git", "init"], cwd=root, check=True,
                           capture_output=True, text=True)
            subprocess.run(["git", "branch", "-m", "main"], cwd=root, check=True,
                           capture_output=True, text=True)
            subprocess.run(["git", "config", "user.email", "t@t.com"],
                           cwd=root, check=True, capture_output=True, text=True)
            subprocess.run(["git", "config", "user.name", "T"],
                           cwd=root, check=True, capture_output=True, text=True)
            subprocess.run(["git", "config", "commit.gpgsign", "false"],
                           cwd=root, check=True, capture_output=True, text=True)

            (root / "main.py").write_text("def f(): pass\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True,
                           capture_output=True, text=True)

            subprocess.run(["git", "checkout", "-b", "feature"], cwd=root, check=True,
                           capture_output=True, text=True)
            (root / "feature.py").write_text("def new(): pass\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "feature"], cwd=root, check=True,
                           capture_output=True, text=True)

            result = compare_branches(str(root), base_ref="main", head_ref="feature")
            self.assertIn("summary", result)
            self.assertIn("risk_delta", result)


if __name__ == "__main__":
    unittest.main()
