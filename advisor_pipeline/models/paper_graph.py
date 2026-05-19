# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Paper graph — builds a NetworkX DiGraph from Advisor pipeline results.

Node types:
    - paper:          The paper itself
    - step:           A logical step in the paper's argument
    - evidence:       An evidence item (figure/math/citation) found for a step
    - figure:         A figure evaluation result
    - math:           A math evaluation result
    - related_paper:  A paper found by the Librarian agent

Edge types:
    - HAS_STEP:     paper -> step
    - DEPENDS_ON:   step -> step
    - SUPPORTS:     evidence -> step
    - ASSESSES:     figure/math -> step
                    (carries location, description, confirmations/contradictions)
    - RELATED_TO:   related_paper -> paper
                    (carries relevancy_score, convergence_score)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx

from advisor_pipeline.models.schemas import (
    Evidence,
    FigureEvaluation,
    LibrarianResult,
    MathEvaluation,
    PaperStructure,
    RelatedPaper,
    StepEvidence,
    ValidationResult,
)


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_paper_graph(
    paper_structure: PaperStructure,
    step_evidence: List[StepEvidence],
    paper_id: str = "unknown",
) -> nx.DiGraph:
    """Build a NetworkX DiGraph from paper structure and evidence.

    Creates paper, step, and evidence nodes.  Evaluation nodes (figure, math,
    citation) should be added later via ``add_figure_evaluations``,
    ``add_math_evaluations``, and ``add_citation_checks``.

    Args:
        paper_structure: Output from map_logic_node.
        step_evidence:   Output from find_evidence_node.
        paper_id:        Unique identifier for the paper.

    Returns:
        A directed graph with paper + step + evidence nodes.
    """
    G = nx.DiGraph()

    # ----- Paper node -----
    paper_node_id = f"paper:{paper_id}"
    G.add_node(
        paper_node_id,
        node_type="paper",
        paper_id=paper_id,
        title=paper_structure.title,
        main_claim=paper_structure.main_claim,
    )

    # ----- LogicalStep nodes + HAS_STEP edges -----
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

        for dep in step.depends_on:
            G.add_edge(step_node_id, f"step:{dep}", edge_type="DEPENDS_ON")

    # ----- Evidence nodes + SUPPORTS edges -----
    for step_ev in step_evidence:
        for ev in step_ev.evidence_list:
            ev_node_id = f"evidence:{ev.evidence_type}:{ev.location}:{ev.supports_step}"
            G.add_node(
                ev_node_id,
                node_type="evidence",
                evidence_type=ev.evidence_type,
                description=ev.description,
                location=ev.location,
                supports_step=ev.supports_step,
                excerpt=ev.excerpt,
            )
            G.add_edge(ev_node_id, f"step:{ev.supports_step}", edge_type="SUPPORTS")

    return G


# ---------------------------------------------------------------------------
# Incremental graph updates — add evaluation results to an existing graph
# ---------------------------------------------------------------------------


def _get_evidence_provenance(G: nx.DiGraph, location: str) -> dict:
    """Look up description + excerpt from evidence nodes matching a location."""
    for _, data in G.nodes(data=True):
        if data.get("node_type") == "evidence" and data.get("location") == location:
            return {"description": data["description"], "excerpt": data.get("excerpt", "")}
    return {"description": "", "excerpt": ""}


def add_figure_evaluations(
    G: nx.DiGraph,
    figure_evaluations: List[FigureEvaluation],
) -> None:
    """Add figure evaluation nodes + ASSESSES edges to an existing graph."""
    for fig_eval in figure_evaluations:
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

        for assessment in fig_eval.claim_assessments:
            step_node_id = f"step:{assessment.supports_step}"
            prov = _get_evidence_provenance(G, fig_eval.figure_name)
            G.add_edge(
                fig_node_id,
                step_node_id,
                edge_type="ASSESSES",
                claim=assessment.claim,
                confirmations=assessment.validity.confirmations,
                contradictions=assessment.validity.contradictions,
                location=fig_eval.figure_name,
                description=prov["description"],
                excerpt=prov["excerpt"],
            )


def add_math_evaluations(
    G: nx.DiGraph,
    math_evaluations: List[MathEvaluation],
) -> None:
    """Add math evaluation nodes + ASSESSES edges to an existing graph."""
    for math_eval in math_evaluations:
        math_node_id = f"math:{math_eval.equation_reference}"
        G.add_node(
            math_node_id,
            node_type="math",
            equation_reference=math_eval.equation_reference,
            calculation_valid=math_eval.calculation_valid,
            details=math_eval.details,
            formula_used=math_eval.formula_used,
        )

        step_node_id = f"step:{math_eval.supports_step}"
        prov = _get_evidence_provenance(G, math_eval.equation_reference)
        G.add_edge(
            math_node_id,
            step_node_id,
            edge_type="ASSESSES",
            location=math_eval.equation_reference,
            description=prov["description"],
            excerpt=prov["excerpt"],
            calculation_valid=math_eval.calculation_valid,
        )


def add_librarian_results(
    G: nx.DiGraph,
    librarian_result: LibrarianResult,
) -> None:
    """Add related-paper nodes + RELATED_TO edges to the paper node."""
    paper_node_id = None
    for nid, data in G.nodes(data=True):
        if data.get("node_type") == "paper":
            paper_node_id = nid
            break
    if paper_node_id is None:
        return

    for rp in librarian_result.related_papers:
        rp_node_id = f"related_paper:{rp.paper_id}"
        G.add_node(
            rp_node_id,
            node_type="related_paper",
            paper_id=rp.paper_id,
            title=rp.title,
            authors=rp.authors,
            abstract=rp.abstract[:500],
            source=rp.source,
            relevancy_score=rp.relevancy_score,
            relevancy_reasoning=rp.relevancy_reasoning,
            convergence_score=rp.convergence_score,
            convergence_reasoning=rp.convergence_reasoning,
        )
        G.add_edge(
            rp_node_id,
            paper_node_id,
            edge_type="RELATED_TO",
            relevancy_score=rp.relevancy_score,
            convergence_score=rp.convergence_score,
        )


def build_graph_from_validation(result: ValidationResult) -> nx.DiGraph:
    """Convenience wrapper to build a graph directly from a ValidationResult."""
    step_evidence = []
    for step_num, validation in result.step_validations.items():
        evidence_list = [Evidence(**ev) for ev in validation.get("evidence", [])]
        step_evidence.append(StepEvidence(step_number=step_num, evidence_list=evidence_list))

    G = build_paper_graph(
        paper_structure=result.paper_structure,
        step_evidence=step_evidence,
        paper_id=result.paper_id,
    )

    figure_evaluations = []
    math_evaluations = []
    for step_num, validation in result.step_validations.items():
        figure_evaluations.extend(
            FigureEvaluation(**f) for f in validation.get("figure_validations", [])
        )
        math_evaluations.extend(
            MathEvaluation(**m) for m in validation.get("math_validations", [])
        )

    add_figure_evaluations(G, figure_evaluations)
    add_math_evaluations(G, math_evaluations)

    # Reconstruct librarian results if present
    librarian_data = result.step_validations.get("librarian", {})
    if librarian_data:
        related_papers = [
            RelatedPaper(**rp) for rp in librarian_data.get("related_papers", [])
        ]
        lib_result = LibrarianResult(
            related_papers=related_papers,
            context_summary=librarian_data.get("context_summary", ""),
            search_queries=librarian_data.get("search_queries", []),
        )
        add_librarian_results(G, lib_result)

    return G


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


def get_nodes_by_type(G: nx.DiGraph, node_type: str) -> list:
    """Return all nodes of a given type as a list of (node_id, data) tuples."""
    return [
        (nid, data) for nid, data in G.nodes(data=True)
        if data.get("node_type") == node_type
    ]


def get_steps(G: nx.DiGraph) -> list:
    """Return all logical step nodes, sorted by step number."""
    return sorted(
        [data for _, data in G.nodes(data=True) if data.get("node_type") == "step"],
        key=lambda s: s["step_number"],
    )


def get_evidence_for_step(G: nx.DiGraph, step_number: int) -> list:
    """Return all evidence node data dicts for a given step (via SUPPORTS edges)."""
    step_node_id = f"step:{step_number}"
    return [
        G.nodes[n]
        for n in G.predecessors(step_node_id)
        if G.nodes[n].get("node_type") == "evidence"
    ]


def get_evaluation_nodes_for_step(G: nx.DiGraph, step_number: int) -> list:
    """Return all figure/math nodes that assess a given step."""
    step_node_id = f"step:{step_number}"
    return [
        G.nodes[n]
        for n in G.predecessors(step_node_id)
        if G.nodes[n].get("node_type") in ("figure", "math")
    ]


def get_steps_with_no_evaluation(G: nx.DiGraph) -> list:
    """Return logical steps that have no figure/math assessments."""
    return [
        data
        for _, data in G.nodes(data=True)
        if data.get("node_type") == "step"
        and not any(
            G.nodes[n].get("node_type") in ("figure", "math")
            for n in G.predecessors(f"step:{data['step_number']}")
        )
    ]


def get_steps_with_no_evidence(G: nx.DiGraph) -> list:
    """Return logical steps that have no evidence nodes (via SUPPORTS edges)."""
    return [
        data
        for _, data in G.nodes(data=True)
        if data.get("node_type") == "step"
        and not any(
            G.nodes[n].get("node_type") == "evidence"
            for n in G.predecessors(f"step:{data['step_number']}")
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
                "figure": G.nodes[u].get("figure_name"),
                "contradictions": data["contradictions"],
            })
    return contradicted


def get_figure_confirmation_counts(G: nx.DiGraph) -> dict:
    """Return total confirmations and contradictions across all figure ASSESSES edges."""
    total_confirmations = 0
    total_contradictions = 0
    for u, v, data in G.edges(data=True):
        if (data.get("edge_type") == "ASSESSES"
                and G.nodes[u].get("node_type") == "figure"):
            total_confirmations += len(data.get("confirmations", []))
            total_contradictions += len(data.get("contradictions", []))
    return {"confirmations": total_confirmations, "contradictions": total_contradictions}


def get_librarian_statistics(G: nx.DiGraph) -> dict:
    """Return statistics about related papers found by the Librarian."""
    rp_nodes = [data for _, data in get_nodes_by_type(G, "related_paper")]
    total = len(rp_nodes)
    if total == 0:
        return {
            "total": 0,
            "avg_relevancy": 0.0,
            "avg_convergence": 0.0,
            "supporting": 0,
            "contradicting": 0,
            "neutral": 0,
        }
    avg_rel = sum(r["relevancy_score"] for r in rp_nodes) / total
    avg_conv = sum(r["convergence_score"] for r in rp_nodes) / total
    supporting = sum(1 for r in rp_nodes if r["convergence_score"] > 0.3)
    contradicting = sum(1 for r in rp_nodes if r["convergence_score"] < -0.3)
    neutral = total - supporting - contradicting
    return {
        "total": total,
        "avg_relevancy": round(avg_rel, 3),
        "avg_convergence": round(avg_conv, 3),
        "supporting": supporting,
        "contradicting": contradicting,
        "neutral": neutral,
    }


def get_related_papers(G: nx.DiGraph) -> list:
    """Return all related-paper nodes sorted by relevancy (descending)."""
    return sorted(
        [data for _, data in get_nodes_by_type(G, "related_paper")],
        key=lambda r: r.get("relevancy_score", 0),
        reverse=True,
    )


def get_high_impact_papers(
    G: nx.DiGraph,
    relevancy_threshold: float = 0.6,
    convergence_threshold: float = 0.5,
) -> list:
    """Return papers with high relevancy AND high |convergence|.

    These are the most important for evaluating the user's paper — highly
    relevant papers whose conclusions either strongly agree or disagree.
    """
    return [
        data
        for _, data in get_nodes_by_type(G, "related_paper")
        if data.get("relevancy_score", 0) >= relevancy_threshold
        and abs(data.get("convergence_score", 0)) >= convergence_threshold
    ]


def get_evidence_by_type(G: nx.DiGraph, evidence_type: str) -> List[Evidence]:
    """Return Evidence objects of the given type from graph evidence nodes."""
    results = []
    for _, data in G.nodes(data=True):
        if data.get("node_type") == "evidence" and data.get("evidence_type") == evidence_type:
            results.append(Evidence(
                evidence_type=data["evidence_type"],
                description=data["description"],
                location=data["location"],
                supports_step=data["supports_step"],
                excerpt=data.get("excerpt", ""),
            ))
    return results


def get_step_claims(G: nx.DiGraph) -> Dict[int, str]:
    """Return a mapping of step number -> description from the graph.

    This is the shape that MathEvaluator.run() expects for its
    ``claims`` parameter.
    """
    return {
        data["step_number"]: data["description"]
        for _, data in G.nodes(data=True)
        if data.get("node_type") == "step"
    }


def get_figure_claims(G: nx.DiGraph) -> Dict[str, list]:
    """Return figure evidence grouped by location, for FigureEvaluator.run().

    Returns:
        Dict mapping figure location -> [{"supports_step": int, "claim": str}]
    """
    figure_claims: Dict[str, list] = {}
    for _, data in G.nodes(data=True):
        if data.get("node_type") == "evidence" and data.get("evidence_type") == "figure":
            location = data["location"]
            step_node_id = f"step:{data['supports_step']}"
            step_data = G.nodes.get(step_node_id, {})
            claim = step_data.get("description", "")
            figure_claims.setdefault(location, []).append({
                "supports_step": data["supports_step"],
                "claim": claim,
            })
    return figure_claims


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
