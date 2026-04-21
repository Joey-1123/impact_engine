from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
import os


def main():
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(BASE_DIR, "tests", "sample.py")

    deps = extract_project_dependencies(file_path)
    graph = build_graph(deps)

    print("Dependencies:", deps)
    print("Graph Edges:", list(graph.edges()))

    # 🔥 Impact test
    target = "a"
    impacted = get_impact(graph, target)

    print(f"\nIf '{target}' changes → impacted functions:")
    print(impacted)


if __name__ == "__main__":
    main()