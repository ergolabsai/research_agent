# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Advisor Pipeline Orchestrator — LangGraph graph with conditional routing.

Pipeline flow:
    START → make_context → gather_papers → map_logic → find_evidence
          → evaluate_figures → evaluate_math → score_papers
          → compile_results → END
"""

import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

import networkx as nx
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from advisor_pipeline.agents.figure_evaluator import FigureEvaluator
from advisor_pipeline.agents.librarian import Librarian
from advisor_pipeline.agents.math_evaluator import MathEvaluator
from core.ports.calculator import Calculator
from core.ports.llm_client import LLMClient
from core.ports.paper_index import PaperIndex
from core.services.prompts import (
    EVIDENCE_FINDER,
    CONTEXT_MAKER,
    LOGIC_MAPPER,
    RESULTS_COMPILER,
    SYSTEM_PROMPT,
)
from advisor_pipeline.models.paper_graph import (
    add_figure_evaluations,
    add_librarian_results,
    add_math_evaluations,
    build_paper_graph,
    get_evidence_by_type,
    get_evidence_for_step,
    get_figure_claims,
    get_figure_confirmation_counts,
    get_high_impact_papers,
    get_invalid_math,
    get_librarian_statistics,
    get_nodes_by_type,
    get_related_papers,
    get_step_claims,
    get_steps,
    save_graph,
)
from advisor_pipeline.models.schemas import (
    FigureEvaluation,
    LibrarianResult,
    MathEvaluation,
    OverAllReview,
    PaperStructure,
    RelatedPaper,
    StepEvidence,
    ValidationResult,
)

# Step callback type: (node_name, state_update_dict, duration_seconds) -> None
StepCallback = Callable[[str, dict, float], None]

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

    # Populated by gather_papers (Librarian pass 1)
    librarian_result: LibrarianResult
    related_papers: list[RelatedPaper]

    # Populated by map_logic
    paper_structure: PaperStructure

    # Populated by find_evidence
    step_evidence: list[StepEvidence]

    # Paper graph (built after find_evidence, updated by evaluation nodes)
    paper_graph: nx.DiGraph

    # Evaluation results
    figure_evaluations: list[FigureEvaluation]
    math_evaluations: list[MathEvaluation]

    # Final output
    validation_result: ValidationResult


# Node implementations live on `AdvisorOrchestrator` (see bottom of file) so
# they can access injected ports via `self`. Pure graph-query helpers stay as
# module-level functions because they only operate on the NetworkX graph.


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

        for pred_id in G.predecessors(step_node_id):
            node = G.nodes[pred_id]
            node_type = node.get("node_type")

            if node_type not in ("figure", "math"):
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

        step_validations[step_num] = {
            "evidence_count": len(ev_list),
            "evidence": ev_list,
            "figure_validations": figure_validations,
            "math_validations": math_validations,
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
        for pred_id in G.predecessors(step_node_id):
            nt = G.nodes[pred_id].get("node_type")
            if nt == "figure":
                fig_count += 1
            elif nt == "math":
                math_count += 1

        lines.append(f"\nStep {step_num}: {step_data['description']}")
        lines.append(f"  Evidence pieces: {ev_count}")
        lines.append(f"  Figure validations: {fig_count}")
        lines.append(f"  Math validations: {math_count}")
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


def _format_librarian_results_from_graph(G: nx.DiGraph) -> str:
    """Format librarian results (related papers) by querying graph nodes."""
    stats = get_librarian_statistics(G)
    if stats["total"] == 0:
        return "No related papers found"

    related = get_related_papers(G)
    high_impact = get_high_impact_papers(G)
    lines = [
        f"Total related papers: {stats['total']}",
        f"Avg relevancy: {stats['avg_relevancy']:.2f}",
        f"Avg convergence: {stats['avg_convergence']:+.2f}",
        f"Supporting: {stats['supporting']}, Contradicting: {stats['contradicting']}, Neutral: {stats['neutral']}",
        f"High-impact papers: {len(high_impact)}",
        "",
    ]
    for rp in related[:10]:
        conv = rp.get('convergence_score', 0)
        rel = rp.get('relevancy_score', 0)
        direction = "supports" if conv > 0.3 else "contradicts" if conv < -0.3 else "neutral"
        lines.append(
            f"- [{rp.get('source', '?')}] {rp.get('title', '?')[:80]}\n"
            f"    Relevancy: {rel:.2f}, Convergence: {conv:+.2f} ({direction})\n"
            f"    {rp.get('convergence_reasoning', '')[:150]}"
        )
    return "\n".join(lines)


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

    # Librarian score: relevancy-weighted convergence
    lib_stats = get_librarian_statistics(G)
    if lib_stats["total"] > 0:
        # High-impact papers (large |convergence| + high relevancy) boost confidence
        # when they agree, reduce it when they disagree
        related = get_related_papers(G)
        weighted_conv = sum(
            r.get("relevancy_score", 0) * r.get("convergence_score", 0)
            for r in related
        )
        total_weight = sum(r.get("relevancy_score", 0) for r in related)
        if total_weight > 0:
            # Map weighted convergence from [-1,1] to [0,1]
            lib_score = (weighted_conv / total_weight + 1) / 2
            scores.append(lib_score)

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
# Public API
# ---------------------------------------------------------------------------


CalculatorFactory = Callable[[], Calculator]


class AdvisorOrchestrator:
    """Main orchestrator for The Advisor validation pipeline.

    Uses a LangGraph StateGraph:

        START -> make_context -> gather_papers -> map_logic -> find_evidence
              -> evaluate_figures -> evaluate_math -> score_papers
              -> compile_results -> END

    Ports are injected at construction time so the orchestrator can be built
    once and reused across many pipeline runs. ``calculator_factory`` is a
    zero-arg callable (typically the ``McpCalculatorClient`` class itself)
    because each run opens its own MCP session via the calculator's sync
    context-manager protocol.
    """

    def __init__(
        self,
        llm: LLMClient,
        paper_index: PaperIndex,
        calculator_factory: CalculatorFactory,
    ):
        print("Initializing Advisor Orchestrator...")
        self._llm = llm
        self._paper_index = paper_index
        self._calculator_factory = calculator_factory
        # Stateless agents — built once, reused across runs.
        self._figure_eval = FigureEvaluator(llm=llm)
        self._librarian = Librarian(llm=llm, paper_index=paper_index)
        # MathEvaluator is *not* built here: its react-agent tools close over
        # the MCP calculator session, which must be opened per-run.
        self._workflow = self._build_graph()
        print("Orchestrator initialized successfully")

    # ------------------------------------------------------------------
    # Node implementations (bound methods so they can access self._*)
    # ------------------------------------------------------------------

    def _make_context_node(self, state: AdvisorState) -> dict:
        """Make context to use going forward."""
        print("STEP 1a: Make some context...")
        context = self._llm.invoke_text(
            CONTEXT_MAKER.format(paper_text=state["paper_text"])
        )
        paper_text = state["paper_text"] + f"\n\n--- Additional Context ---\n{context}"
        return {"paper_text": paper_text}

    def _map_logic_node(self, state: AdvisorState) -> dict:
        """Identify the logical structure of the paper."""
        print("STEP 1b: Identifying logical steps...")
        paper_structure = self._llm.get_structured_output(
            PaperStructure,
            LOGIC_MAPPER.format(paper_text=state["paper_text"]),
            system_prompt=SYSTEM_PROMPT,
        )
        print(f"  Identified {len(paper_structure.logical_steps)} logical steps")
        return {"paper_structure": paper_structure}

    def _find_evidence_node(self, state: AdvisorState) -> dict:
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
            step_evidence = self._llm.get_structured_output(
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

        paper_graph = build_paper_graph(
            paper_structure=paper_structure,
            step_evidence=all_step_evidence,
            paper_id=state.get("paper_id", "unknown"),
        )
        print(
            f"  Built paper graph: {paper_graph.number_of_nodes()} nodes, "
            f"{paper_graph.number_of_edges()} edges"
        )

        return {
            "step_evidence": all_step_evidence,
            "paper_graph": paper_graph,
        }

    def _evaluate_figures_node(self, state: AdvisorState) -> dict:
        """Evaluate figure-based evidence."""
        print("STEP 3a: Evaluating figure-based evidence...")
        figures = state.get("figures", {})
        G = state["paper_graph"]
        figure_claims = get_figure_claims(G)

        figure_evaluations = self._figure_eval.run(
            figures=figures,
            figure_claims=figure_claims,
            paper_text=state["paper_text"],
        )
        print(f"  Evaluated {len(figure_evaluations)} figures")

        add_figure_evaluations(G, figure_evaluations)
        return {"figure_evaluations": figure_evaluations, "paper_graph": G}

    def _evaluate_math_node(self, state: AdvisorState) -> dict:
        """Evaluate math-based evidence."""
        print("STEP 3b: Evaluating math-based evidence...")
        G = state["paper_graph"]
        math_evidence = get_evidence_by_type(G, "math")
        claims = get_step_claims(G)

        # Per-run MCP session: each pipeline owns its own calculator client.
        with self._calculator_factory() as client:
            evaluator = MathEvaluator(llm=self._llm, calculator=client)
            math_evaluations = evaluator.run(
                evidence_list=math_evidence,
                paper_text=state["paper_text"],
                claims=claims,
            )
        print(f"  Evaluated {len(math_evaluations)} math items")

        add_math_evaluations(G, math_evaluations)
        return {"math_evaluations": math_evaluations, "paper_graph": G}

    def _gather_papers_node(self, state: AdvisorState) -> dict:
        """Librarian pass 1: find cited + related papers, enrich context."""
        print("STEP 1b: Librarian gathering related papers...")
        librarian_result = self._librarian.gather_papers(
            paper_text=state["paper_text"],
            bibliography=state.get("bibliography", {}),
            paper_structure=state.get("paper_structure"),
        )
        print(f"  Found {len(librarian_result.related_papers)} related papers")
        print(f"  Search queries used: {librarian_result.search_queries}")

        enriched = state["paper_text"]
        if librarian_result.context_summary:
            enriched += f"\n\n--- Related Work Context ---\n{librarian_result.context_summary}"

        return {
            "paper_text": enriched,
            "librarian_result": librarian_result,
            "related_papers": librarian_result.related_papers,
        }

    def _score_papers_node(self, state: AdvisorState) -> dict:
        """Librarian pass 2: score each related paper for relevancy + convergence."""
        print("STEP 3c: Scoring related papers...")
        related_papers = state.get("related_papers", [])
        paper_structure = state["paper_structure"]

        if not related_papers:
            print("  No related papers to score")
            return {"librarian_result": state.get("librarian_result", LibrarianResult())}

        scored = self._librarian.score_papers(
            paper_text=state["paper_text"],
            paper_structure=paper_structure,
            related_papers=related_papers,
        )
        print(f"  Scored {len(scored)} papers")

        lib_result = state.get("librarian_result", LibrarianResult())
        updated_result = LibrarianResult(
            related_papers=scored,
            context_summary=lib_result.context_summary,
            search_queries=lib_result.search_queries,
        )

        G = state["paper_graph"]
        add_librarian_results(G, updated_result)
        return {"librarian_result": updated_result, "paper_graph": G}

    def _compile_results_node(self, state: AdvisorState) -> dict:
        """Compile all evaluation results into a final assessment."""
        print("STEP 4: Compiling final assessment...")
        paper_structure: PaperStructure = state["paper_structure"]
        G = state["paper_graph"]

        step_validations = _organize_by_step_from_graph(G)
        num_figure_evals = len(get_nodes_by_type(G, "figure"))
        num_math_evals = len(get_nodes_by_type(G, "math"))
        num_related_papers = len(get_nodes_by_type(G, "related_paper"))

        review_prompt = RESULTS_COMPILER.format(
            paper_title=paper_structure.title,
            main_claim=paper_structure.main_claim,
            num_steps=len(paper_structure.logical_steps),
            num_figure_evals=num_figure_evals,
            num_math_evals=num_math_evals,
            num_related_papers=num_related_papers,
            step_validations_text=_format_step_validations(G),
            figure_results_text=_format_figure_results_from_graph(G),
            math_results_text=_format_math_results_from_graph(G),
            librarian_results_text=_format_librarian_results_from_graph(G),
        )
        overall_review = self._llm.get_structured_output(
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

        output_folder = state.get("output_folder")
        if output_folder:
            graph_path = Path(output_folder) / "paper_graph.json"
            save_graph(G, graph_path)
            print(f"  Paper graph saved to {graph_path}")

        return {"validation_result": result, "paper_graph": G}

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _node_funcs(self) -> Dict[str, Callable[[AdvisorState], dict]]:
        """Single source of truth for node-name -> bound-method mapping.

        Both `_build_graph` and `_build_graph_with_callbacks` read from here
        so the two stay in sync when nodes are added or renamed.
        """
        return {
            "make_context": self._make_context_node,
            "gather_papers": self._gather_papers_node,
            "map_logic": self._map_logic_node,
            "find_evidence": self._find_evidence_node,
            "evaluate_figures": self._evaluate_figures_node,
            "evaluate_math": self._evaluate_math_node,
            "score_papers": self._score_papers_node,
            "compile_results": self._compile_results_node,
        }

    @staticmethod
    def _add_edges(workflow: StateGraph) -> None:
        workflow.add_edge(START, "make_context")
        workflow.add_edge("make_context", "gather_papers")
        workflow.add_edge("gather_papers", "map_logic")
        workflow.add_edge("map_logic", "find_evidence")
        workflow.add_edge("find_evidence", "evaluate_figures")
        workflow.add_edge("evaluate_figures", "evaluate_math")
        workflow.add_edge("evaluate_math", "score_papers")
        workflow.add_edge("score_papers", "compile_results")
        workflow.add_edge("compile_results", END)

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AdvisorState)
        for name, fn in self._node_funcs().items():
            workflow.add_node(name, fn)
        self._add_edges(workflow)
        return workflow

    def _build_graph_with_callbacks(self, callback: StepCallback) -> StateGraph:
        """Build a fresh graph whose nodes time + report progress to `callback`."""

        def _wrap(name, fn):
            def wrapper(state: AdvisorState) -> dict:
                t0 = time.time()
                result = fn(state)
                duration = time.time() - t0
                try:
                    callback(name, result, duration)
                except Exception:
                    pass  # never let logging break the pipeline
                return result
            return wrapper

        workflow = StateGraph(AdvisorState)
        for name, fn in self._node_funcs().items():
            workflow.add_node(name, _wrap(name, fn))
        self._add_edges(workflow)
        return workflow

    # ------------------------------------------------------------------
    # Public run() entry point
    # ------------------------------------------------------------------

    def run(
        self,
        paper_text: str = None,
        figures: Dict[str, Dict[str, str]] = None,
        paper_bib: Dict[str, str] | None = None,
        output_folder: str | Path | None = None,
        on_step_complete: Optional[StepCallback] = None,
    ) -> ValidationResult:
        """Run the complete validation pipeline on a paper.

        Args:
            paper_text: Full text of the paper.
            figures: Dict mapping figure names to image data.
            paper_bib: Dict of citation references.
            output_folder: Folder path to save the final paper graph JSON.
            on_step_complete: Optional callback invoked after each node with
                (node_name, state_update, duration_seconds). Stays a per-run
                arg because it typically closes over job_id.

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
        }

        if on_step_complete:
            graph = self._build_graph_with_callbacks(on_step_complete).compile()
        else:
            graph = self._workflow.compile()

        final_state = graph.invoke(initial_state)

        print(f"\n{'=' * 60}")
        print("Pipeline complete!")
        print(f"{'=' * 60}\n")

        return final_state["validation_result"]
