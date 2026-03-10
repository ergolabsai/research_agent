"""Advisor Pipeline Orchestrator — LangGraph graph with conditional routing.

Replaces the old linear pipeline.py with a flexible graph that supports:
- Context enrichment loop (make_context -> find_evidence -> loop back if needed)
- Conditional evaluation routing (figures, math, citations — only branches with evidence)
- All evaluation types enabled (figures, math, citations)
"""

from pathlib import Path
from typing import Dict

import networkx as nx
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from advisor_pipeline.llm import get_structured_output, invoke_text
from advisor_pipeline.mcp_servers.advisor_server.prompts import (
    EVIDENCE_FINDER,
    CONTEXT_MAKER,
    LOGIC_MAPPER,
    RESULTS_COMPILER,
    SYSTEM_PROMPT,
)
from advisor_pipeline.models.paper_graph import (
    add_citation_checks,
    add_figure_evaluations,
    add_math_evaluations,
    build_paper_graph,
    get_citation_statistics,
    get_evidence_by_type,
    get_evidence_for_step,
    get_figure_claims,
    get_figure_confirmation_counts,
    get_invalid_math,
    get_nodes_by_type,
    get_step_claims,
    get_steps,
    save_graph,
)
from advisor_pipeline.models.schemas import (
    CitationCheck,
    FigureEvaluation,
    MathEvaluation,
    OverAllReview,
    PaperStructure,
    StepEvidence,
    ValidationResult,
)

# ---------------------------------------------------------------------------
# Pipeline state
# ---------------------------------------------------------------------------


class AdvisorState(TypedDict, total=False):
    # Inputs
    paper_text: str
    figures: Dict[str, Dict[str, str]]
    bibliography: Dict[str, str]
    output_folder: str  # folder path to save the final paper graph

    # Populated by make_context
    paper_context: str

    # Populated by map_logic
    paper_structure: PaperStructure

    # Populated by find_evidence
    step_evidence: list[StepEvidence]

    # Paper graph (built after find_evidence, updated by evaluation nodes)
    paper_graph: nx.DiGraph

    # Evaluation results
    figure_evaluations: list[FigureEvaluation]
    math_evaluations: list[MathEvaluation]
    citation_checks: list[CitationCheck]

    # Final output
    validation_result: ValidationResult


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------


def make_context_node(state: AdvisorState) -> dict:
    """make context to use going forward."""
    print("STEP 1a: Make some context...")
    context = invoke_text(
        CONTEXT_MAKER.format(
            paper_text=state["paper_text"],
        )
    )
    # Append enrichment to paper text as additional context
    paper_text = state["paper_text"] + f"\n\n--- Additional Context ---\n{context}"

    return {
        "paper_text": paper_text,
    }


def map_logic_node(state: AdvisorState) -> dict:
    """Identify the logical structure of the paper."""
    print("STEP 1b: Identifying logical steps...")
    paper_structure = get_structured_output(
        PaperStructure,
        LOGIC_MAPPER.format(paper_text=state["paper_text"]),
        system_prompt=SYSTEM_PROMPT,
    )
    print(f"  Identified {len(paper_structure.logical_steps)} logical steps")

    return {"paper_structure": paper_structure}


def find_evidence_node(state: AdvisorState) -> dict:
    """Find evidence supporting each logical step (ALL steps, no cap)."""
    print("STEP 2: Finding evidence for each logical step...")
    paper_structure: PaperStructure = state["paper_structure"]
    paper_text: str = state["paper_text"]
    figure_names = list(state.get("figures", {}).keys())
    figure_names_str = ", ".join(figure_names) if figure_names else "None provided"

    all_step_evidence: list[StepEvidence] = []
    sorted_steps = sorted(paper_structure.logical_steps, key=lambda s: s.step_number)

    for step in sorted_steps:
        print(f"  Finding evidence for step {step.step_number}: {step.description[:100]}...")
        step_evidence = get_structured_output(
            StepEvidence,
            EVIDENCE_FINDER.format(
                step_number=step.step_number,
                step_description=step.description,
                step_section=step.section,
                figure_names=figure_names_str,
                paper_text=paper_text,
            ),
            system_prompt=SYSTEM_PROMPT,
        )
        step_evidence.step_number = step.step_number
        all_step_evidence.append(step_evidence)

    total_evidence = sum(len(se.evidence_list) for se in all_step_evidence)
    print(f"  Found {total_evidence} pieces of evidence across all steps")

    # Build the paper graph from structure + evidence
    paper_graph = build_paper_graph(
        paper_structure=paper_structure,
        step_evidence=all_step_evidence,
        paper_id=state.get("paper_id", "unknown"),
    )
    print(f"  Built paper graph: {paper_graph.number_of_nodes()} nodes, {paper_graph.number_of_edges()} edges")

    return {
        "step_evidence": all_step_evidence,
        "paper_graph": paper_graph,
    }


def evaluate_figures_node(state: AdvisorState) -> dict:
    """Evaluate figure-based evidence."""
    from advisor_pipeline.agents.figure_evaluator import FigureEvaluator

    print("STEP 3a: Evaluating figure-based evidence...")
    figures = state.get("figures", {})

    # Query the paper graph for figure claims
    G = state["paper_graph"]
    figure_claims = get_figure_claims(G)

    evaluator = FigureEvaluator()
    figure_evaluations = evaluator.run(
        figures=figures,
        figure_claims=figure_claims,
        paper_text=state["paper_text"],
    )
    print(f"  Evaluated {len(figure_evaluations)} figures")

    # Add evaluation results to the graph
    add_figure_evaluations(G, figure_evaluations)

    return {"figure_evaluations": figure_evaluations, "paper_graph": G}


def evaluate_math_node(state: AdvisorState) -> dict:
    """Evaluate math-based evidence."""
    from advisor_pipeline.agents.math_evaluator import MathEvaluator
    from advisor_pipeline.mcp_client import CalculatorClient

    print("STEP 3b: Evaluating math-based evidence...")

    # Query the paper graph for math evidence and step claims
    G = state["paper_graph"]
    math_evidence = get_evidence_by_type(G, "math")
    claims = get_step_claims(G)

    with CalculatorClient() as client:
        evaluator = MathEvaluator(mcp_client=client)
        math_evaluations = evaluator.run(
            evidence_list=math_evidence,
            paper_text=state["paper_text"],
            claims=claims,
        )
    print(f"  Evaluated {len(math_evaluations)} math items")

    # Add evaluation results to the graph
    add_math_evaluations(G, math_evaluations)

    return {"math_evaluations": math_evaluations, "paper_graph": G}


def check_citations_node(state: AdvisorState) -> dict:
    """Check citation-based evidence."""
    from advisor_pipeline.agents.citation_checker import CitationChecker

    print("STEP 3c: Checking citations...")

    # Query the paper graph for citation evidence and step claims
    G = state["paper_graph"]
    citation_evidence = get_evidence_by_type(G, "citation")
    claims = get_step_claims(G)

    checker = CitationChecker()
    citation_checks = checker.run(
        evidence_list=citation_evidence,
        paper_text=state["paper_text"],
        claims=claims,
        bibliography=state.get("bibliography", {}),
    )
    print(f"  Checked {len(citation_checks)} citations")

    # Add evaluation results to the graph
    add_citation_checks(G, citation_checks)

    return {"citation_checks": citation_checks, "paper_graph": G}


def compile_results_node(state: AdvisorState) -> dict:
    """Compile all evaluation results into a final assessment."""
    print("STEP 4: Compiling final assessment...")
    paper_structure: PaperStructure = state["paper_structure"]

    # Use the graph that has been incrementally updated by evaluation nodes
    G = state["paper_graph"]

    # Organize validations by step using graph queries
    step_validations = _organize_by_step_from_graph(G)

    # Count evaluations from graph nodes
    num_figure_evals = len(get_nodes_by_type(G, "figure"))
    num_math_evals = len(get_nodes_by_type(G, "math"))
    num_citation_checks = len(get_nodes_by_type(G, "citation"))

    # Generate overall review
    review_prompt = RESULTS_COMPILER.format(
        paper_title=paper_structure.title,
        main_claim=paper_structure.main_claim,
        num_steps=len(paper_structure.logical_steps),
        num_figure_evals=num_figure_evals,
        num_math_evals=num_math_evals,
        num_citation_checks=num_citation_checks,
        step_validations_text=_format_step_validations(G),
        figure_results_text=_format_figure_results_from_graph(G),
        math_results_text=_format_math_results_from_graph(G),
        citation_results_text=_format_citation_results_from_graph(G),
    )

    overall_review = get_structured_output(
        OverAllReview, review_prompt, system_prompt=SYSTEM_PROMPT
    )

    confidence_score = _calculate_confidence_from_graph(G)

    result = ValidationResult(
        paper_id=state.get("paper_id", "unknown"),
        paper_structure=paper_structure,
        step_validations=step_validations,
        overall_assessment=overall_review,
        confidence_score=confidence_score,
    )
    print(f"  Final confidence score: {result.confidence_score:.2%}")

    # Save graph to output folder
    output_folder = state.get("output_folder")
    if output_folder:
        graph_path = Path(output_folder) / "paper_graph.json"
        save_graph(G, graph_path)
        print(f"  Paper graph saved to {graph_path}")

    return {"validation_result": result, "paper_graph": G}


# ---------------------------------------------------------------------------
# Helpers — query the paper graph instead of iterating flat lists
# ---------------------------------------------------------------------------


def _organize_by_step_from_graph(G: nx.DiGraph) -> Dict[int, Dict]:
    """Build step_validations dict by querying graph nodes and edges."""
    step_validations: Dict[int, Dict] = {}

    for step_data in get_steps(G):
        step_num = step_data["step_number"]
        step_node_id = f"step:{step_num}"

        # Get evidence from SUPPORTS edges in the graph
        ev_nodes = get_evidence_for_step(G, step_num)
        ev_list = [
            {
                "evidence_type": ev["evidence_type"],
                "description": ev["description"],
                "location": ev["location"],
                "supports_step": ev["supports_step"],
                "excerpt": ev.get("excerpt", ""),
            }
            for ev in ev_nodes
        ]

        figure_validations = []
        math_validations = []
        citation_validations = []

        for pred_id in G.predecessors(step_node_id):
            node = G.nodes[pred_id]
            node_type = node.get("node_type")

            if node_type not in ("figure", "math", "citation"):
                continue

            edge_data = G.edges[pred_id, step_node_id]

            if node_type == "figure":
                figure_validations.append({
                    "figure_name": node["figure_name"],
                    "actual_description": node["actual_description"],
                    "expected_description": node["expected_description"],
                    "comparison": {
                        "similarities": node["similarities"],
                        "differences": node["differences"],
                    },
                    "claim_assessments": [{
                        "supports_step": step_num,
                        "claim": edge_data.get("claim", ""),
                        "validity": {
                            "confirmations": edge_data.get("confirmations", []),
                            "contradictions": edge_data.get("contradictions", []),
                        },
                    }],
                })

            elif node_type == "math":
                math_validations.append({
                    "equation_reference": node["equation_reference"],
                    "supports_step": step_num,
                    "calculation_valid": node["calculation_valid"],
                    "details": node["details"],
                    "formula_used": node.get("formula_used"),
                })

            elif node_type == "citation":
                citation_validations.append({
                    "citation": node["citation"],
                    "supports_step": step_num,
                    "accessible": node["accessible"],
                    "supports_claim": node["supports_claim"],
                    "notes": node.get("notes", ""),
                })

        step_validations[step_num] = {
            "evidence_count": len(ev_list),
            "evidence": ev_list,
            "figure_validations": figure_validations,
            "math_validations": math_validations,
            "citation_validations": citation_validations,
        }

    return step_validations


def _format_step_validations(G: nx.DiGraph) -> str:
    """Format step validations summary by querying the graph."""
    lines = []
    for step_data in get_steps(G):
        step_num = step_data["step_number"]
        step_node_id = f"step:{step_num}"

        ev_count = len(get_evidence_for_step(G, step_num))
        fig_count = 0
        math_count = 0
        cit_count = 0
        for pred_id in G.predecessors(step_node_id):
            nt = G.nodes[pred_id].get("node_type")
            if nt == "figure":
                fig_count += 1
            elif nt == "math":
                math_count += 1
            elif nt == "citation":
                cit_count += 1

        lines.append(f"\nStep {step_num}: {step_data['description']}")
        lines.append(f"  Evidence pieces: {ev_count}")
        lines.append(f"  Figure validations: {fig_count}")
        lines.append(f"  Math validations: {math_count}")
        lines.append(f"  Citation checks: {cit_count}")
    return "\n".join(lines)


def _format_figure_results_from_graph(G: nx.DiGraph) -> str:
    """Format figure evaluation results by querying graph nodes and edges."""
    figure_nodes = get_nodes_by_type(G, "figure")
    if not figure_nodes:
        return "No figure evaluations performed"

    lines = []
    for fig_id, fig_data in figure_nodes:
        lines.append(f"\n- {fig_data['figure_name']}:")
        lines.append(f"  Actual: {fig_data['actual_description'][:150]}...")
        lines.append(f"  Expected: {fig_data['expected_description'][:150]}...")
        lines.append(
            f"  Similarities: {len(fig_data['similarities'])}, "
            f"Differences: {len(fig_data['differences'])}"
        )
        for _, step_id, edge_data in G.edges(fig_id, data=True):
            if edge_data.get("edge_type") == "ASSESSES":
                step_num = G.nodes[step_id].get("step_number", "?")
                conf = len(edge_data.get("confirmations", []))
                cont = len(edge_data.get("contradictions", []))
                lines.append(
                    f"  Step {step_num}: {conf} confirmations, {cont} contradictions"
                )
    return "\n".join(lines)


def _format_math_results_from_graph(G: nx.DiGraph) -> str:
    """Format math evaluation results by querying graph nodes."""
    math_nodes = [data for _, data in get_nodes_by_type(G, "math")]
    if not math_nodes:
        return "No math evaluations performed"

    valid_count = sum(1 for m in math_nodes if m["calculation_valid"])
    lines = [f"Valid calculations: {valid_count}/{len(math_nodes)}"]
    for m in math_nodes:
        status = "Valid" if m["calculation_valid"] else "Invalid"
        lines.append(f"- {m['equation_reference']}: {status}")
    return "\n".join(lines)


def _format_citation_results_from_graph(G: nx.DiGraph) -> str:
    """Format citation check results by querying graph nodes."""
    stats = get_citation_statistics(G)
    if stats["total"] == 0:
        return "No citation checks performed"

    return (
        f"Accessible citations: {stats['accessible']}/{stats['total']}\n"
        f"Citations supporting claims: {stats['supporting']}/"
        f"{stats['accessible'] if stats['accessible'] > 0 else 'N/A'}"
    )


def _calculate_confidence_from_graph(G: nx.DiGraph) -> float:
    """Calculate confidence score by querying graph nodes and edges."""
    scores = []

    # Math score: fraction of valid calculations
    all_math = [data for _, data in get_nodes_by_type(G, "math")]
    if all_math:
        invalid = get_invalid_math(G)
        math_score = (len(all_math) - len(invalid)) / len(all_math)
        scores.append(math_score)

    # Figure score: confirmations vs contradictions
    fig_counts = get_figure_confirmation_counts(G)
    total_assessments = fig_counts["confirmations"] + fig_counts["contradictions"]
    if total_assessments > 0:
        fig_score = fig_counts["confirmations"] / total_assessments
        scores.append(fig_score)

    # Citation score: fraction of accessible citations that support their claim
    cit_stats = get_citation_statistics(G)
    if cit_stats["accessible"] > 0:
        cit_score = cit_stats["supporting"] / cit_stats["accessible"]
        scores.append(cit_score)

    # Coverage score: fraction of steps that have evidence (from SUPPORTS edges)
    all_steps = get_steps(G)
    if all_steps:
        steps_with_ev = sum(
            1 for s in all_steps
            if get_evidence_for_step(G, s["step_number"])
        )
        coverage_score = steps_with_ev / len(all_steps)
        scores.append(coverage_score)

    return sum(scores) / len(scores) if scores else 0.5


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def _build_graph() -> StateGraph:
    workflow = StateGraph(AdvisorState)

    # Add nodes
    workflow.add_node("make_context", make_context_node)
    workflow.add_node("map_logic", map_logic_node)
    workflow.add_node("find_evidence", find_evidence_node)
    workflow.add_node("evaluate_figures", evaluate_figures_node)
    workflow.add_node("evaluate_math", evaluate_math_node)
    workflow.add_node("check_citations", check_citations_node)
    workflow.add_node("compile_results", compile_results_node)

    # Edges
    workflow.add_edge(START, "make_context")
    workflow.add_edge("make_context", "map_logic")
    workflow.add_edge("map_logic", "find_evidence")
    workflow.add_edge("find_evidence", "evaluate_figures")
    workflow.add_edge("evaluate_figures", "evaluate_math")
    workflow.add_edge("evaluate_math", "check_citations")
    workflow.add_edge("check_citations", "compile_results")
    workflow.add_edge("compile_results", END)

    return workflow


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class AdvisorOrchestrator:
    """Main orchestrator for The Advisor validation pipeline.

    Uses a LangGraph StateGraph with conditional routing:

        START -> make_context -> map_logic -> find_evidence
          find_evidence -> [conditional]
            -> make_context (if more context needed, max 2 loops)
            -> route_evaluations
          route_evaluations -> [conditional]
            -> evaluate_figures / evaluate_math / check_citations
          evaluate_* -> compile_results -> END
    """

    def __init__(self):
        print("Initializing Advisor Orchestrator...")
        self._graph = _build_graph().compile()
        print("Orchestrator initialized successfully")

    def run(
        self,
        paper_text: str = None,
        figures: Dict[str, Dict[str, str]] = None,
        paper_bib: Dict[str, str] | None = None,
        output_folder: str | Path | None = None,
    ) -> ValidationResult:
        """Run the complete validation pipeline on a paper.

        Args:
            paper_text: Full text of the paper.
            figures: Dict mapping figure names to image data.
            paper_bib: Dict of citation references.
            output_folder: Folder path to save the final paper graph JSON.

        Returns:
            ValidationResult with complete assessment.
        """
        print(f"\n{'=' * 60}")
        print("Running validation pipeline")
        print(f"{'=' * 60}\n")

        initial_state: AdvisorState = {
            "paper_text": paper_text,
            "figures": figures,
            "bibliography": paper_bib or {},
            "output_folder": str(output_folder) if output_folder else "",
            "figure_evaluations": [],
            "math_evaluations": [],
            "citation_checks": [],
        }

        final_state = self._graph.invoke(initial_state)

        print(f"\n{'=' * 60}")
        print("Pipeline complete!")
        print(f"{'=' * 60}\n")

        return final_state["validation_result"]
