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
    build_paper_graph,
    get_evidence_by_type,
    get_figure_claims,
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

    # Paper graph (built after find_evidence, used by evaluation nodes)
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
    return {"figure_evaluations": figure_evaluations}


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
    return {"math_evaluations": math_evaluations}


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
    return {"citation_checks": citation_checks}


def compile_results_node(state: AdvisorState) -> dict:
    """Compile all evaluation results into a final assessment."""
    print("STEP 4: Compiling final assessment...")
    paper_structure: PaperStructure = state["paper_structure"]
    step_evidence: list[StepEvidence] = state.get("step_evidence", [])
    figure_evals: list[FigureEvaluation] = state.get("figure_evaluations", [])
    math_evals: list[MathEvaluation] = state.get("math_evaluations", [])
    citation_checks: list[CitationCheck] = state.get("citation_checks", [])

    # Build final graph with all evaluation results
    G = build_paper_graph(
        paper_structure=paper_structure,
        step_evidence=step_evidence,
        figure_evaluations=figure_evals,
        math_evaluations=math_evals,
        citation_checks=citation_checks,
        paper_id=state.get("paper_id", "unknown"),
    )

    # Organize validations by step using graph queries
    step_validations = _organize_by_step_from_graph(G, step_evidence)

    # Count evaluations from graph nodes
    num_figure_evals = sum(
        1 for _, d in G.nodes(data=True) if d.get("node_type") == "figure"
    )
    num_math_evals = sum(
        1 for _, d in G.nodes(data=True) if d.get("node_type") == "math"
    )
    num_citation_checks = sum(
        1 for _, d in G.nodes(data=True) if d.get("node_type") == "citation"
    )

    # Generate overall review
    review_prompt = RESULTS_COMPILER.format(
        paper_title=paper_structure.title,
        main_claim=paper_structure.main_claim,
        num_steps=len(paper_structure.logical_steps),
        num_figure_evals=num_figure_evals,
        num_math_evals=num_math_evals,
        num_citation_checks=num_citation_checks,
        step_validations_text=_format_step_validations(step_validations, paper_structure),
        figure_results_text=_format_figure_results_from_graph(G),
        math_results_text=_format_math_results_from_graph(G),
        citation_results_text=_format_citation_results_from_graph(G),
    )

    overall_review = get_structured_output(
        OverAllReview, review_prompt, system_prompt=SYSTEM_PROMPT
    )

    confidence_score = _calculate_confidence_from_graph(G, step_validations)

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


def _organize_by_step_from_graph(
    G: nx.DiGraph,
    step_evidence: list[StepEvidence],
) -> Dict[int, Dict]:
    """Build step_validations dict by querying graph nodes and edges."""
    # Build evidence lookup from step_evidence (evidence items aren't in the graph)
    evidence_by_step: Dict[int, list] = {}
    for se in step_evidence:
        evidence_by_step[se.step_number] = [ev.model_dump() for ev in se.evidence_list]

    step_validations: Dict[int, Dict] = {}

    for step_data in get_steps(G):
        step_num = step_data["step_number"]
        step_node_id = f"step:{step_num}"
        ev_list = evidence_by_step.get(step_num, [])

        figure_validations = []
        math_validations = []
        citation_validations = []

        for pred_id in G.predecessors(step_node_id):
            node = G.nodes[pred_id]
            node_type = node.get("node_type")
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


def _format_step_validations(
    step_validations: Dict[int, Dict],
    paper_structure: PaperStructure,
) -> str:
    lines = []
    for step in paper_structure.logical_steps:
        step_num = step.step_number
        validation = step_validations.get(step_num, {})
        lines.append(f"\nStep {step_num}: {step.description}")
        lines.append(f"  Evidence pieces: {validation.get('evidence_count', 0)}")
        lines.append(f"  Figure validations: {len(validation.get('figure_validations', []))}")
        lines.append(f"  Math validations: {len(validation.get('math_validations', []))}")
        lines.append(f"  Citation checks: {len(validation.get('citation_validations', []))}")
    return "\n".join(lines)


def _format_figure_results_from_graph(G: nx.DiGraph) -> str:
    """Format figure evaluation results by querying graph nodes and edges."""
    figure_nodes = [
        (nid, data) for nid, data in G.nodes(data=True)
        if data.get("node_type") == "figure"
    ]
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
        # Each outgoing ASSESSES edge represents a claim assessment for a step
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
    math_nodes = [
        data for _, data in G.nodes(data=True)
        if data.get("node_type") == "math"
    ]
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
    citation_nodes = [
        data for _, data in G.nodes(data=True)
        if data.get("node_type") == "citation"
    ]
    if not citation_nodes:
        return "No citation checks performed"

    accessible_count = sum(1 for c in citation_nodes if c["accessible"])
    supported_count = sum(1 for c in citation_nodes if c["supports_claim"] is True)
    return (
        f"Accessible citations: {accessible_count}/{len(citation_nodes)}\n"
        f"Citations supporting claims: {supported_count}/"
        f"{accessible_count if accessible_count > 0 else 'N/A'}"
    )


def _calculate_confidence_from_graph(
    G: nx.DiGraph,
    step_validations: Dict,
) -> float:
    """Calculate confidence score by querying graph nodes and edges."""
    scores = []

    # Math score: fraction of valid calculations
    math_nodes = [
        data for _, data in G.nodes(data=True)
        if data.get("node_type") == "math"
    ]
    if math_nodes:
        math_score = sum(1 for m in math_nodes if m["calculation_valid"]) / len(math_nodes)
        scores.append(math_score)

    # Figure score: confirmations vs contradictions from ASSESSES edges
    figure_nodes = [
        nid for nid, data in G.nodes(data=True)
        if data.get("node_type") == "figure"
    ]
    if figure_nodes:
        total_confirmations = 0
        total_contradictions = 0
        for fig_id in figure_nodes:
            for _, _, edge_data in G.edges(fig_id, data=True):
                if edge_data.get("edge_type") == "ASSESSES":
                    total_confirmations += len(edge_data.get("confirmations", []))
                    total_contradictions += len(edge_data.get("contradictions", []))
        if total_confirmations + total_contradictions > 0:
            fig_score = total_confirmations / (total_confirmations + total_contradictions)
            scores.append(fig_score)

    # Citation score: fraction of accessible citations that support their claim
    citation_nodes = [
        data for _, data in G.nodes(data=True)
        if data.get("node_type") == "citation"
    ]
    if citation_nodes:
        accessible = [c for c in citation_nodes if c["accessible"]]
        if accessible:
            cit_score = sum(1 for c in accessible if c["supports_claim"]) / len(accessible)
            scores.append(cit_score)

    # Coverage score: fraction of steps that have evidence
    if step_validations:
        steps_with_evidence = sum(
            1 for v in step_validations.values() if v.get("evidence_count", 0) > 0
        )
        coverage_score = steps_with_evidence / len(step_validations)
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
