"""Advisor Pipeline Orchestrator — LangGraph graph with conditional routing.

Replaces the old linear pipeline.py with a flexible graph that supports:
- Context enrichment loop (make_context -> find_evidence -> loop back if needed)
- Conditional evaluation routing (figures, math, citations — only branches with evidence)
- All evaluation types enabled (figures, math, citations)
"""

from pathlib import Path
from typing import Any, Dict, Optional

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from advisor_pipeline.database import Database
from advisor_pipeline.llm import get_structured_output, invoke_text
from advisor_pipeline.mcp_servers.advisor_server.prompts import (
    EVIDENCE_FINDER,
    CONTEXT_MAKER,
    LOGIC_MAPPER,
    RESULTS_COMPILER,
    SYSTEM_PROMPT,
)
from advisor_pipeline.models.schemas import (
    CitationCheck,
    FigureEvaluation,
    MathEvaluation,
    OverAllReview,
    PaperDocument,
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
    save_to_db: bool

    # Populated by make_context
    paper_context: str

    # Populated by map_logic
    paper_structure: PaperStructure

    # Populated by find_evidence
    step_evidence: list[StepEvidence]
    evaluation_types_needed: list[str]

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

    # Optionally save to database
    if state.get("save_to_db"):
        try:
            db = Database()
            db.connect()
            paper_doc = PaperDocument(
                paper_id=state["paper_id"],
                title=paper_structure.title,
                authors=[],
                abstract="",
                full_text=state["paper_text"],
            )
            db.save_paper(paper_doc)
            db.disconnect()
            print("  Paper saved to database")
        except Exception as e:
            print(f"  Warning: could not save paper to DB: {e}")

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

    # Determine which evaluation branches are needed
    has_figures = any(
        ev.evidence_type == "figure" for se in all_step_evidence for ev in se.evidence_list
    )
    has_math = any(
        ev.evidence_type == "math" for se in all_step_evidence for ev in se.evidence_list
    )
    has_citations = any(
        ev.evidence_type == "citation" for se in all_step_evidence for ev in se.evidence_list
    )

    eval_types = []
    if has_figures:
        eval_types.append("figures")
    # if has_math:
    #     eval_types.append("math")
    # if has_citations:
    #     eval_types.append("citations")

    return {
        "step_evidence": all_step_evidence,
        "evaluation_types_needed": eval_types,
    }


def evaluate_figures_node(state: AdvisorState) -> dict:
    """Evaluate figure-based evidence."""
    from advisor_pipeline.agents.figure_evaluator import FigureEvaluator

    print("STEP 3a: Evaluating figure-based evidence...")
    paper_structure: PaperStructure = state["paper_structure"]
    figures = state.get("figures", {})
    step_evidence = state["step_evidence"]

    # Build figure-to-claims mapping
    figure_claims: Dict[str, list] = {}
    for se in step_evidence:
        for ev in se.evidence_list:
            if ev.evidence_type == "figure":
                if ev.location not in figure_claims:
                    figure_claims[ev.location] = []
                figure_claims[ev.location].append(
                    {
                        "supports_step": ev.supports_step,
                        "claim": paper_structure.logical_steps[ev.supports_step-1].description
                    }
                )

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

    print("STEP 3b: Evaluating math-based evidence...")
    paper_structure: PaperStructure = state["paper_structure"]
    step_evidence = state["step_evidence"]

    # Collect all math evidence
    math_evidence = []
    for se in step_evidence:
        for ev in se.evidence_list:
            if ev.evidence_type == "math":
                math_evidence.append(ev)

    claims = {step.step_number: step.description for step in paper_structure.logical_steps}

    evaluator = MathEvaluator()
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
    paper_structure: PaperStructure = state["paper_structure"]
    step_evidence = state["step_evidence"]

    # Collect all citation evidence
    citation_evidence = []
    for se in step_evidence:
        for ev in se.evidence_list:
            if ev.evidence_type == "citation":
                citation_evidence.append(ev)

    claims = {step.step_number: step.description for step in paper_structure.logical_steps}

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

    # Organize validations by step
    step_validations = _organize_by_step(step_evidence, figure_evals, math_evals, citation_checks)

    # Generate overall review
    review_prompt = RESULTS_COMPILER.format(
        paper_title=paper_structure.title,
        main_claim=paper_structure.main_claim,
        num_steps=len(paper_structure.logical_steps),
        num_figure_evals=len(figure_evals),
        num_math_evals=len(math_evals),
        num_citation_checks=len(citation_checks),
        step_validations_text=_format_step_validations(step_validations, paper_structure),
        figure_results_text=_format_figure_results(figure_evals),
        math_results_text=_format_math_results(math_evals),
        citation_results_text=_format_citation_results(citation_checks),
    )

    overall_review = get_structured_output(
        OverAllReview, review_prompt, system_prompt=SYSTEM_PROMPT
    )

    confidence_score = _calculate_confidence(
        figure_evals, math_evals, citation_checks, step_validations
    )

    result = ValidationResult(
        paper_id=state.get("paper_id", "unknown"),
        paper_structure=paper_structure,
        step_validations=step_validations,
        overall_assessment=overall_review,
        confidence_score=confidence_score,
    )
    print(f"  Final confidence score: {result.confidence_score:.2%}")

    # Save to database
    if state.get("save_to_db"):
        try:
            db = Database()
            db.connect()
            db.save_validation(result, state["paper_id"])
            db.disconnect()
            print("  Validation saved to database")
        except Exception as e:
            print(f"  Warning: could not save validation to DB: {e}")

    return {"validation_result": result}


# ---------------------------------------------------------------------------
# Helpers (absorbed from ResultsCompilerAgent)
# ---------------------------------------------------------------------------


def _organize_by_step(
    step_evidence: list[StepEvidence],
    figure_evals: list[FigureEvaluation],
    math_evals: list[MathEvaluation],
    citation_checks: list[CitationCheck],
) -> Dict[int, Dict[str, Any]]:
    step_validations: Dict[int, Dict[str, Any]] = {}

    for step_ev in step_evidence:
        step_num = step_ev.step_number
        step_validations[step_num] = {
            "evidence_count": len(step_ev.evidence_list),
            "evidence": [ev.model_dump() for ev in step_ev.evidence_list],
            "figure_validations": [],
            "math_validations": [],
            "citation_validations": [],
        }

    for fig_eval in figure_evals:
        for assessment in fig_eval.claim_assessments:
            step_num = assessment.supports_step
            if step_num in step_validations:
                step_validations[step_num]["figure_validations"].append(fig_eval.model_dump())

    for math_eval in math_evals:
        step_num = math_eval.supports_step
        if step_num in step_validations:
            step_validations[step_num]["math_validations"].append(math_eval.model_dump())

    for cit_check in citation_checks:
        step_num = cit_check.supports_step
        if step_num in step_validations:
            step_validations[step_num]["citation_validations"].append(cit_check.model_dump())

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


def _format_figure_results(figure_evals: list[FigureEvaluation]) -> str:
    if not figure_evals:
        return "No figure evaluations performed"
    lines = []
    for fig in figure_evals:
        lines.append(f"\n- {fig.figure_name}:")
        lines.append(f"  Actual: {fig.actual_description[:150]}...")
        lines.append(f"  Expected: {fig.expected_description[:150]}...")
        lines.append(
            f"  Similarities: {len(fig.comparison.similarities)}, "
            f"Differences: {len(fig.comparison.differences)}"
        )
        for assessment in fig.claim_assessments:
            conf = len(assessment.validity.confirmations)
            cont = len(assessment.validity.contradictions)
            lines.append(
                f"  Step {assessment.supports_step}: {conf} confirmations, {cont} contradictions"
            )
    return "\n".join(lines)


def _format_math_results(math_evals: list[MathEvaluation]) -> str:
    if not math_evals:
        return "No math evaluations performed"
    valid_count = sum(1 for m in math_evals if m.calculation_valid)
    lines = [f"Valid calculations: {valid_count}/{len(math_evals)}"]
    for math in math_evals:
        status = "Valid" if math.calculation_valid else "Invalid"
        lines.append(f"- {math.equation_reference}: {status}")
    return "\n".join(lines)


def _format_citation_results(citation_checks: list[CitationCheck]) -> str:
    if not citation_checks:
        return "No citation checks performed"
    accessible_count = sum(1 for c in citation_checks if c.accessible)
    supported_count = sum(1 for c in citation_checks if c.supports_claim is True)
    return (
        f"Accessible citations: {accessible_count}/{len(citation_checks)}\n"
        f"Citations supporting claims: {supported_count}/"
        f"{accessible_count if accessible_count > 0 else 'N/A'}"
    )


def _calculate_confidence(
    figure_evals: list[FigureEvaluation],
    math_evals: list[MathEvaluation],
    citation_checks: list[CitationCheck],
    step_validations: Dict,
) -> float:
    scores = []

    if math_evals:
        math_score = sum(1 for m in math_evals if m.calculation_valid) / len(math_evals)
        scores.append(math_score)

    if figure_evals:
        total_confirmations = sum(
            len(a.validity.confirmations) for f in figure_evals for a in f.claim_assessments
        )
        total_contradictions = sum(
            len(a.validity.contradictions) for f in figure_evals for a in f.claim_assessments
        )
        if total_confirmations + total_contradictions > 0:
            fig_score = total_confirmations / (total_confirmations + total_contradictions)
            scores.append(fig_score)

    if citation_checks:
        accessible = [c for c in citation_checks if c.accessible]
        if accessible:
            cit_score = sum(1 for c in accessible if c.supports_claim) / len(accessible)
            scores.append(cit_score)

    if step_validations:
        steps_with_evidence = sum(
            1 for v in step_validations.values() if v.get("evidence_count", 0) > 0
        )
        coverage_score = steps_with_evidence / len(step_validations)
        scores.append(coverage_score)

    return sum(scores) / len(scores) if scores else 0.5


# ---------------------------------------------------------------------------
# Conditional routing functions
# ---------------------------------------------------------------------------


def get_evaluation_branches(state: AdvisorState) -> list[str]:
    """Determine which evaluation branches to run based on evidence found."""
    eval_types = state.get("evaluation_types_needed", [])
    branches = []
    if "figures" in eval_types:
        branches.append("evaluate_figures")
    # if "math" in eval_types:
    #     branches.append("evaluate_math")
    # if "citations" in eval_types:
    #     branches.append("check_citations")
    if not branches:
        branches.append("compile_results")
    return branches


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
    # workflow.add_node("evaluate_math", evaluate_math_node)
    # workflow.add_node("check_citations", check_citations_node)
    workflow.add_node("compile_results", compile_results_node)

    # Edges
    workflow.add_edge(START, "make_context")
    workflow.add_edge("make_context", "map_logic")
    workflow.add_edge("map_logic", "find_evidence")


    #COMENTING OUT OTHER TYPES OF CHECKS FOR NOW
    # Conditional: route to evaluation branches
    # workflow.add_conditional_edges(
    #     "find_evidence",
    #     get_evaluation_branches,
    #     {
    #         "evaluate_figures": "evaluate_figures",
    #         "evaluate_math": "evaluate_math",
    #         "check_citations": "check_citations",
    #         "compile_results": "compile_results",
    #     },
    # )

    workflow.add_edge("find_evidence", "evaluate_figures")

    # All evaluation branches converge on compile_results
    workflow.add_edge("evaluate_figures", "compile_results")
    # workflow.add_edge("evaluate_math", "compile_results")
    # workflow.add_edge("check_citations", "compile_results")
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

    def __init__(self, db: Database | None = None):
        print("Initializing Advisor Orchestrator...")
        self.db = db
        if self.db:
            self.db.connect()
        self._graph = _build_graph().compile()
        print("Orchestrator initialized successfully")

    def run(
        self,
        paper_text: str = None,
        figures: Dict[str, Dict[str, str]] = None,
        paper_bib: Dict[str, str] | None = None,
        save_to_db: bool = True,
    ) -> ValidationResult:
        """Run the complete validation pipeline on a paper.

        Args:
            paper_id: Unique identifier for the paper.
            paper_folder: Path to the folder containing main_text.tex and images/.
            save_to_db: Whether to save results to database.
            bibliography: Dict of citation references.

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
            "save_to_db": save_to_db,
            "figure_evaluations": [],
            "math_evaluations": [],
            "citation_checks": [],
        }

        final_state = self._graph.invoke(initial_state)

        print(f"\n{'=' * 60}")
        print("Pipeline complete!")
        print(f"{'=' * 60}\n")

        return final_state["validation_result"]

    def load_from_database(self, paper_id: str) -> Optional[ValidationResult]:
        """Load the latest validation for a paper from database."""
        if not self.db:
            raise ValueError("Database not initialized")
        return self.db.get_latest_validation(paper_id)

    def __del__(self):
        if self.db:
            self.db.disconnect()
