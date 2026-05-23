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


class SummaryTests(unittest.TestCase):
    def test_summary_ranks_high_risk_nodes_first(self):
        class DummyGraph:
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
        class DummyGraph:
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


if __name__ == "__main__":
    unittest.main()
