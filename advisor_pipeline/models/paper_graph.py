"""Paper graph — builds a NetworkX DiGraph from Advisor pipeline results.

Node types:
    - paper:        The paper itself
    - step:         A logical step in the paper's argument
    - evidence:     A piece of evidence supporting a step
    - figure:       A figure evaluation result
    - math:         A math evaluation result
    - citation:     A citation check result

Edge types:
    - HAS_STEP:         paper -> step
    - DEPENDS_ON:       step -> step
    - SUPPORTED_BY:     step -> evidence
    - IS_FIGURE:        evidence -> figure
    - IS_MATH:          evidence -> math
    - IS_CITATION:      evidence -> citation
    - ASSESSES:         figure -> step  (carries confirmations/contradictions)
"""

import json
from pathlib import Path
from typing import List, Optional

import networkx as nx

from advisor_pipeline.models.schemas import (
    CitationCheck,
    FigureEvaluation,
    MathEvaluation,
    PaperStructure,
    StepEvidence,
    ValidationResult,
)


def build_paper_graph(
    paper_structure: PaperStructure,
    step_evidence: List[StepEvidence],
    figure_evaluations: Optional[List[FigureEvaluation]] = None,
    math_evaluations: Optional[List[MathEvaluation]] = None,
    citation_checks: Optional[List[CitationCheck]] = None,
    paper_id: str = "unknown",
) -> nx.DiGraph:
    """Build a NetworkX DiGraph from Advisor pipeline results.

    Args:
        paper_structure:     Output from map_logic_node.
        step_evidence:       Output from find_evidence_node.
        figure_evaluations:  Output from evaluate_figures_node (optional).
        math_evaluations:    Output from evaluate_math_node (optional).
        citation_checks:     Output from check_citations_node (optional).
        paper_id:            Unique identifier for the paper.

    Returns:
        A directed graph representing the paper's logical structure and evidence.
    """
    G = nx.DiGraph()

    # -------------------------------------------------------------------------
    # Paper node
    # -------------------------------------------------------------------------
    paper_node_id = f"paper:{paper_id}"
    G.add_node(
        paper_node_id,
        node_type="paper",
        paper_id=paper_id,
        title=paper_structure.title,
        main_claim=paper_structure.main_claim,
    )

    # -------------------------------------------------------------------------
    # LogicalStep nodes + HAS_STEP edges
    # -------------------------------------------------------------------------
    for step in paper_structure.logical_steps:
        step_node_id = f"step:{step.step_number}"
        G.add_node(
            step_node_id,
            node_type="step",
            step_number=step.step_number,
            description=step.description,
            section=step.section,
        )
        G.add_edge(paper_node_id, step_node_id, edge_type="HAS_STEP")

        # DEPENDS_ON edges between steps
        for dep in step.depends_on:
            G.add_edge(step_node_id, f"step:{dep}", edge_type="DEPENDS_ON")

    # -------------------------------------------------------------------------
    # Evidence nodes + SUPPORTED_BY edges
    # -------------------------------------------------------------------------
    evidence_counts = {}  # track count per step for unique node ids

    for step_ev in step_evidence:
        step_node_id = f"step:{step_ev.step_number}"
        for ev in step_ev.evidence_list:
            # Build a unique evidence node id
            count = evidence_counts.get(step_ev.step_number, 0)
            evidence_node_id = f"evidence:{step_ev.step_number}:{count}"
            evidence_counts[step_ev.step_number] = count + 1

            G.add_node(
                evidence_node_id,
                node_type="evidence",
                evidence_type=ev.evidence_type,
                description=ev.description,
                location=ev.location,
                supports_step=ev.supports_step,
            )
            G.add_edge(step_node_id, evidence_node_id, edge_type="SUPPORTED_BY")

    # -------------------------------------------------------------------------
    # Figure evaluation nodes + IS_FIGURE and ASSESSES edges
    # -------------------------------------------------------------------------
    for fig_eval in (figure_evaluations or []):
        fig_node_id = f"figure:{fig_eval.figure_name}"
        G.add_node(
            fig_node_id,
            node_type="figure",
            figure_name=fig_eval.figure_name,
            actual_description=fig_eval.actual_description,
            expected_description=fig_eval.expected_description,
            similarities=fig_eval.comparison.similarities,
            differences=fig_eval.comparison.differences,
        )

        # Connect figure to its evidence node(s) via IS_FIGURE
        for node_id, data in G.nodes(data=True):
            if (
                data.get("node_type") == "evidence"
                and data.get("evidence_type") == "figure"
                and data.get("location") == fig_eval.figure_name
            ):
                G.add_edge(node_id, fig_node_id, edge_type="IS_FIGURE")

        # ASSESSES edges: figure -> step, with claim validity as edge properties
        for assessment in fig_eval.claim_assessments:
            step_node_id = f"step:{assessment.supports_step}"
            G.add_edge(
                fig_node_id,
                step_node_id,
                edge_type="ASSESSES",
                claim=assessment.claim,
                confirmations=assessment.validity.confirmations,
                contradictions=assessment.validity.contradictions,
            )

    # -------------------------------------------------------------------------
    # Math evaluation nodes + IS_MATH edges
    # -------------------------------------------------------------------------
    for i, math_eval in enumerate(math_evaluations or []):
        math_node_id = f"math:{i}:{math_eval.equation_reference}"
        G.add_node(
            math_node_id,
            node_type="math",
            equation_reference=math_eval.equation_reference,
            supports_step=math_eval.supports_step,
            calculation_valid=math_eval.calculation_valid,
            details=math_eval.details,
            formula_used=math_eval.formula_used,
        )

        # Connect math to its evidence node(s) via IS_MATH
        for node_id, data in G.nodes(data=True):
            if (
                data.get("node_type") == "evidence"
                and data.get("evidence_type") == "math"
                and data.get("location") == math_eval.equation_reference
            ):
                G.add_edge(node_id, math_node_id, edge_type="IS_MATH")

    # -------------------------------------------------------------------------
    # Citation check nodes + IS_CITATION edges
    # -------------------------------------------------------------------------
    for i, cit_check in enumerate(citation_checks or []):
        cit_node_id = f"citation:{i}:{cit_check.citation[:40]}"
        G.add_node(
            cit_node_id,
            node_type="citation",
            citation=cit_check.citation,
            supports_step=cit_check.supports_step,
            accessible=cit_check.accessible,
            supports_claim=cit_check.supports_claim,
            notes=cit_check.notes,
        )

        # Connect citation to its evidence node(s) via IS_CITATION
        for node_id, data in G.nodes(data=True):
            if (
                data.get("node_type") == "evidence"
                and data.get("evidence_type") == "citation"
                and data.get("location") == cit_check.citation
            ):
                G.add_edge(node_id, cit_node_id, edge_type="IS_CITATION")

    return G


def build_graph_from_validation(result: ValidationResult) -> nx.DiGraph:
    """Convenience wrapper to build a graph directly from a ValidationResult.

    Args:
        result: The completed ValidationResult from the pipeline.

    Returns:
        A directed graph representing the paper's logical structure and evidence.
    """
    # Extract step evidence from step_validations dict
    step_evidence = []
    for step_num, validation in result.step_validations.items():
        from advisor_pipeline.models.schemas import Evidence, StepEvidence
        evidence_list = [Evidence(**ev) for ev in validation.get("evidence", [])]
        step_evidence.append(StepEvidence(step_number=step_num, evidence_list=evidence_list))

    # Extract evaluation results
    figure_evaluations = []
    math_evaluations = []
    citation_checks = []
    for step_num, validation in result.step_validations.items():
        figure_evaluations.extend(
            FigureEvaluation(**f) for f in validation.get("figure_validations", [])
        )
        math_evaluations.extend(
            MathEvaluation(**m) for m in validation.get("math_validations", [])
        )
        citation_checks.extend(
            CitationCheck(**c) for c in validation.get("citation_validations", [])
        )

    return build_paper_graph(
        paper_structure=result.paper_structure,
        step_evidence=step_evidence,
        figure_evaluations=figure_evaluations,
        math_evaluations=math_evaluations,
        citation_checks=citation_checks,
        paper_id=result.paper_id,
    )


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def save_graph(G: nx.DiGraph, path: Path) -> None:
    """Save graph to JSON using node-link format."""
    data = nx.node_link_data(G)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_graph(path: Path) -> nx.DiGraph:
    """Load graph from JSON node-link format."""
    with open(path) as f:
        data = json.load(f)
    return nx.node_link_graph(data, directed=True)


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def get_steps(G: nx.DiGraph) -> list:
    """Return all logical step nodes, sorted by step number."""
    return sorted(
        [data for _, data in G.nodes(data=True) if data.get("node_type") == "step"],
        key=lambda s: s["step_number"],
    )


def get_evidence_for_step(G: nx.DiGraph, step_number: int) -> list:
    """Return all evidence nodes connected to a given step."""
    step_node_id = f"step:{step_number}"
    return [
        G.nodes[n]
        for n in G.successors(step_node_id)
        if G.nodes[n].get("node_type") == "evidence"
    ]


def get_steps_with_no_evidence(G: nx.DiGraph) -> list:
    """Return logical steps that have no supporting evidence."""
    return [
        data
        for _, data in G.nodes(data=True)
        if data.get("node_type") == "step"
        and not any(
            G.nodes[n].get("node_type") == "evidence"
            for n in G.successors(f"step:{data['step_number']}")
        )
    ]


def get_invalid_math(G: nx.DiGraph) -> list:
    """Return all math nodes where calculation_valid is False."""
    return [
        data
        for _, data in G.nodes(data=True)
        if data.get("node_type") == "math" and not data.get("calculation_valid")
    ]


def get_contradicted_steps(G: nx.DiGraph) -> list:
    """Return steps where a figure assessment found contradictions."""
    contradicted = []
    for u, v, data in G.edges(data=True):
        if data.get("edge_type") == "ASSESSES" and data.get("contradictions"):
            contradicted.append({
                "step": G.nodes[v],
                "figure": G.nodes[u]["figure_name"],
                "contradictions": data["contradictions"],
            })
    return contradicted


def get_dependency_chain(G: nx.DiGraph, step_number: int) -> list:
    """Return all steps that a given step depends on, recursively."""
    step_node_id = f"step:{step_number}"
    ancestors = nx.ancestors(G, step_node_id)
    return sorted(
        [
            G.nodes[n]
            for n in ancestors
            if G.nodes[n].get("node_type") == "step"
        ],
        key=lambda s: s["step_number"],
    )