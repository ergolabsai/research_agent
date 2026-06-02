#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Example usage of The Advisor pipeline.

This script demonstrates how to:
1. Set up the orchestrator with database
2. Run validation on a paper
3. Retrieve and display results
4. Query the paper graph for insights
"""

from pathlib import Path

from core.services.orchestrator import AdvisorOrchestrator
from core.domain.graph import (
    get_contradicted_steps,
    get_dependency_chain,
    get_invalid_math,
    get_citation_statistics,
    get_nodes_by_type,
    get_steps,
    get_steps_with_no_evaluation,
    get_steps_with_no_evidence,
    load_graph,
)
from utils import load_paper


def example_basic_usage():
    """Basic example: Run pipeline on a paper without database."""

    paper_folder = Path('/Users/chelsea/python_projects/project_files/shumlak2009_latex')

    loaded_paper = load_paper.load_paper_from_file(
        paper_file=paper_folder / 'main_text.tex',
        figure_folder=paper_folder / 'images',
        bib_file=paper_folder / 'bib.tex')

    # Initialize orchestrator (no database for this basic example)
    orchestrator = AdvisorOrchestrator()

    # Run validation

    result = orchestrator.run(
        paper_text=loaded_paper["paper_text"],
        figures=loaded_paper["figures"],
        paper_bib=loaded_paper["bib_text"],
        output_folder=paper_folder,
    )

    # Display results
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    print(f"Main Claim: {result.paper_structure.main_claim}")
    print(f"Logical Steps: {len(result.paper_structure.logical_steps)}")
    print(f"Confidence Score: {result.confidence_score:.2%}")
    print(f"\nOverall Review:\n{result.overall_assessment.review}")
    print("=" * 60 + "\n")

    # --- Graph-based analysis ---
    print("=" * 60)
    print("GRAPH ANALYSIS")
    print("=" * 60)

    graph_path = paper_folder / "paper_graph.json"
    if graph_path.exists():
        G = load_graph(graph_path)
        _print_graph_analysis(G)

    return result


def _print_graph_analysis(G):
    """Demonstrate graph query helpers on a completed paper graph."""

    # Node counts
    for node_type in ("step", "evidence", "figure", "math", "citation"):
        count = len(get_nodes_by_type(G, node_type))
        print(f"  {node_type} nodes: {count}")

    # Steps with no evidence
    gaps = get_steps_with_no_evidence(G)
    if gaps:
        print(f"\nSteps with NO evidence ({len(gaps)}):")
        for s in gaps:
            print(f"  Step {s['step_number']}: {s['description'][:80]}")

    # Steps with no evaluations
    unevaluated = get_steps_with_no_evaluation(G)
    if unevaluated:
        print(f"\nSteps with NO evaluations ({len(unevaluated)}):")
        for s in unevaluated:
            print(f"  Step {s['step_number']}: {s['description'][:80]}")

    # Contradicted steps
    contradictions = get_contradicted_steps(G)
    if contradictions:
        print(f"\nContradicted steps ({len(contradictions)}):")
        for c in contradictions:
            step_num = c["step"].get("step_number", "?")
            print(f"  Step {step_num} (figure: {c['figure']}):")
            for item in c["contradictions"]:
                print(f"    - {item}")
    else:
        print("\nNo contradictions found.")

    # Invalid math
    invalid = get_invalid_math(G)
    if invalid:
        print(f"\nInvalid math ({len(invalid)}):")
        for m in invalid:
            print(f"  {m['equation_reference']}: {m['details'][:100]}")
    else:
        print("No invalid math found.")

    # Citation statistics
    cit_stats = get_citation_statistics(G)
    print(f"\nCitation stats: {cit_stats['accessible']}/{cit_stats['total']} accessible, "
          f"{cit_stats['supporting']} supporting claims")

    # Dependency chain for the last step
    steps = get_steps(G)
    if steps:
        last_step = steps[-1]["step_number"]
        chain = get_dependency_chain(G, last_step)
        if chain:
            print(f"\nDependency chain for step {last_step} ({len(chain)} ancestors):")
            for s in chain:
                print(f"  Step {s['step_number']}: {s['description'][:80]}")

    print()


if __name__ == "__main__":
    print("The Advisor Pipeline - Example Usage\n")

    # Choose which example to run
    print("Running basic example...")
    result = example_basic_usage()

    print("\nDone!")
