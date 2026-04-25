from core.extractor import extract_project_dependencies
from core.graph_builder import build_graph
from core.traversal import get_impact
from core.visualizer import print_impact_tree, visualize_graph
from core.analyzer import calculate_risk, find_dead_code
import os


def main():
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(BASE_DIR, "tests", "sample.py")

    deps = extract_project_dependencies(file_path)
    graph = build_graph(deps)

    print("Dependencies:", deps)
    print("Graph Edges:", list(graph.edges()))

    # ✅ Generate graph image FIRST
    visualize_graph(graph)
    print("Graph saved as graph.png")

    # 🔥 Impact test
    target = "a"

    matches = [node for node in graph.nodes if node.endswith(f"::{target}")]

    if not matches:
        print(f"Function '{target}' not found.")
        return

    for match in matches:
        print(f"\nImpact Tree for '{match}':")
        print_impact_tree(graph, match)

# 🔥 Dead code detection
    dead = find_dead_code(graph)

    print("\nDead Code (unused functions):")
    for d in dead:

        print(f"- {d}")
        risk = calculate_risk(graph, match)
        print(f"\nRisk Score for '{match}': {risk}")

if __name__ == "__main__":
    main()