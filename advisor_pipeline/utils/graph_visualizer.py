"""Visualize a paper graph as an interactive HTML network using pyvis."""

from advisor_pipeline.models.paper_graph import (
    get_nodes_by_type,
    get_steps,
    load_graph,
)

from pyvis.network import Network


def build_network(G, output_path: str) -> None:
    """Build a pyvis Network from a paper graph and write to HTML."""
    net = Network(directed=True)

    # Color scheme by node type
    colors = {
        "paper": "#4A90D9",
        "step": "#7ED321",
        "evidence": "#F5A623",
        "figure": "#BD10E0",
        "math": "#D0021B",
        "citation": "#50E3C2",
    }

    for node_id, data in G.nodes(data=True):
        node_type = data.get("node_type", "")
        color = colors.get(node_type, "#999999")

        if node_type == "figure":
            title = (
                f"Figure: {data.get('figure_name')}\n\n"
                f"Actual: {data.get('actual_description')}\n\n"
                f"Expected: {data.get('expected_description')}\n\n"
                f"Similarities:\n" + "\n".join(f"  - {s}" for s in data.get("similarities", [])) +
                f"\n\nDifferences:\n" + "\n".join(f"  - {d}" for d in data.get("differences", []))
            )
        elif node_type == "step":
            title = f"Step {data.get('step_number')}: {data.get('description')}"
        elif node_type == "evidence":
            title = f"Evidence ({data.get('evidence_type')}): {data.get('description')}"
        elif node_type == "math":
            title = f"{data.get('equation_reference')}\nValid: {data.get('calculation_valid')}\n{data.get('details')}"
        elif node_type == "citation":
            title = f"{data.get('citation')}\nAccessible: {data.get('accessible')}\nSupports claim: {data.get('supports_claim')}"
        elif node_type == "paper":
            title = f"{data.get('title')}\n{data.get('main_claim')}"
        else:
            title = str(data)

        net.add_node(node_id, label=node_id, title=title, color=color)

    for u, v, data in G.edges(data=True):
        net.add_edge(u, v, title=data.get("edge_type", ""))

    net.write_html(output_path)


if __name__ == "__main__":
    G = load_graph("/Users/chelsea/python_projects/project_files/shumlak2009_latex/paper_graph.json")
    build_network(G, "/Users/chelsea/python_projects/project_files/shumlak2009_latex/paper_graph.html")
