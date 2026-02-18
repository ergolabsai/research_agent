from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image
import io
import base64

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from advisor_pipeline.agents.logic_mapping_agent import LogicMappingAgent
from advisor_pipeline.agents.evidence_finder_agent import EvidenceFinderAgent
from advisor_pipeline.agents.figure_evaluator_agent import FigureEvaluatorAgent
from advisor_pipeline.agents.math_evaluator_agent import MathEvaluatorAgent
from advisor_pipeline.agents.citation_checker_agent import CitationCheckerAgent
from advisor_pipeline.agents.results_compiler_agent import ResultsCompilerAgent

from advisor_pipeline.models.schemas import (
    PaperDocument,
    ValidationResult,
    PaperStructure,
    StepEvidence,
    FigureEvaluation,
    MathEvaluation,
    CitationCheck,
)
from advisor_pipeline.database import Database


def encode_image(image_path: Path, max_size=800) -> tuple[str, str]:
    # Resize if image is larger than max_size

    # Open the image
    img = Image.open(image_path)

    if max(img.size) > max_size:
        # Calculate new size maintaining aspect ratio
        ratio = max_size / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Determine format and media type from extension
    if image_path.name.endswith('.png'):
        img_format = "PNG"
        media_type = "image/png"
    elif image_path.name.endswith('.jpg') or image_path.name.endswith('.jpeg'):
        img_format = "JPEG"
        media_type = "image/jpeg"
    elif image_path.name.endswith('.gif'):
        img_format = "GIF"
        media_type = "image/gif"
    elif image_path.name.endswith('.webp'):
        img_format = "WEBP"
        media_type = "image/webp"
    else:
        img_format = "JPEG"
        media_type = "image/jpeg"

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format=img_format)
    image_data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

    return image_data, media_type


# ---------------------------------------------------------------------------
# Pipeline state — every node reads from / writes to this TypedDict
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    # Inputs (set before the graph runs)
    paper_id: str
    paper_folder: Path
    save_to_db: bool
    bibliography: Dict[str, str]

    # Populated by load_paper
    paper_text: str
    figures: Dict[str, Dict[str, str]]

    # Populated by map_logic
    paper_structure: PaperStructure

    # Populated by find_evidence
    step_evidence: list[StepEvidence]

    # Populated by evaluate_figures
    figure_evaluations: list[FigureEvaluation]

    # Steps 4 & 5 are currently disabled. When re-enabled they would
    # run in parallel with evaluate_figures, before compile_results.
    # math_evaluations: list[MathEvaluation]
    # citation_checks: list[CitationCheck]

    # Populated by compile_results
    validation_result: ValidationResult


class AdvisorPipeline:
    """
    Main orchestrator for The Advisor validation pipeline.

    Uses a LangGraph StateGraph to run the pipeline:

        START -> load_paper -> map_logic -> find_evidence
              -> evaluate_figures -> compile_results -> END

    Steps 4 (math) and 5 (citations) are currently disabled.  When
    re-enabled they would slot in as parallel nodes alongside
    evaluate_figures, before compile_results.
    """

    def __init__(self, mcp_client=None, db: Database = None):
        """
        Initialize the pipeline with all agents.

        Args:
            mcp_client: MCP calculator client (required for math validation)
            db: Database instance (optional, for persistence)
        """
        print("Initializing Advisor Pipeline...")

        # Initialize database
        self.db = db
        if self.db:
            self.db.connect()

        # Initialize all agents
        print("Loading agents...")
        self.logic_mapper = LogicMappingAgent()
        self.evidence_finder = EvidenceFinderAgent()
        self.figure_evaluator = FigureEvaluatorAgent()
        self.math_evaluator = MathEvaluatorAgent(mcp_client=mcp_client)
        self.citation_checker = CitationCheckerAgent()
        self.results_compiler = ResultsCompilerAgent()

        # Build the pipeline graph
        self._graph = self._build_graph()

        print("Pipeline initialized successfully")

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self) -> Any:
        """Build and compile the LangGraph pipeline."""
        workflow = StateGraph(PipelineState)

        workflow.add_node("load_paper", self._node_load_paper)
        workflow.add_node("map_logic", self._node_map_logic)
        workflow.add_node("find_evidence", self._node_find_evidence)
        workflow.add_node("evaluate_figures", self._node_evaluate_figures)
        workflow.add_node("compile_results", self._node_compile_results)

        workflow.add_edge(START, "load_paper")
        workflow.add_edge("load_paper", "map_logic")
        workflow.add_edge("map_logic", "find_evidence")
        workflow.add_edge("find_evidence", "evaluate_figures")
        workflow.add_edge("evaluate_figures", "compile_results")
        workflow.add_edge("compile_results", END)

        return workflow.compile()

    # ------------------------------------------------------------------
    # Node functions — each reads from state and returns updates
    # ------------------------------------------------------------------

    def _node_load_paper(self, state: PipelineState) -> dict:
        """Load paper text and figures from disk."""
        print("STEP 1a: Loading paper from disk...")
        paper_folder = Path(state["paper_folder"])

        paper_path = paper_folder / "main_text.tex"
        with open(paper_path, 'r') as f:
            paper_text = f.read()

        figures: Dict[str, Dict[str, str]] = {}
        image_folder = paper_folder / 'images'
        if image_folder.exists():
            for img_path in image_folder.iterdir():
                if img_path.is_file():
                    img_data, media_type = encode_image(img_path)
                    figures[img_path.name] = {'data': img_data, 'media_type': media_type}

        return {"paper_text": paper_text, "figures": figures}

    def _node_map_logic(self, state: PipelineState) -> dict:
        """Identify the logical structure of the paper."""
        print("STEP 1b: Identifying logical steps...")
        paper_structure = self.logic_mapper.run({
            "paper_text": state["paper_text"]
        })
        print(f"  Identified {len(paper_structure.logical_steps)} logical steps")

        # Optionally save to database
        if state.get("save_to_db") and self.db:
            paper_doc = PaperDocument(
                paper_id=state["paper_id"],
                title=paper_structure.main_claim,
                authors=[],
                abstract="",
                full_text=state["paper_text"],
                figures=state.get("figures") or {}
            )
            self.db.save_paper(paper_doc)
            print("  Paper saved to database")

        return {"paper_structure": paper_structure}

    def _node_find_evidence(self, state: PipelineState) -> dict:
        """Find evidence supporting each logical step."""
        print("STEP 2: Finding evidence for each logical step...")
        figure_names = list(state.get("figures", {}).keys())
        step_evidence = self.evidence_finder.run({
            "paper_structure": state["paper_structure"],
            "paper_text": state["paper_text"],
            "figure_names": figure_names
        })
        total_evidence = sum(len(se.evidence_list) for se in step_evidence)
        print(f"  Found {total_evidence} pieces of evidence across all steps")
        return {"step_evidence": step_evidence}

    def _node_evaluate_figures(self, state: PipelineState) -> dict:
        """Evaluate figure-based evidence."""
        print("STEP 3: Evaluating figure-based evidence...")
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
                    figure_claims[ev.location].append({
                        "supports_step": ev.supports_step,
                        "claim": next(
                            (step.description for step in paper_structure.logical_steps
                             if step.step_number == ev.supports_step),
                            "Unknown claim"
                        )
                    })

        figure_evaluations = self.figure_evaluator.run({
            "figures": figures,
            "figure_claims": figure_claims,
            "paper_text": state["paper_text"]
        })
        print(f"  Evaluated {len(figure_evaluations)} figures")
        return {"figure_evaluations": figure_evaluations}

    def _node_compile_results(self, state: PipelineState) -> dict:
        """Compile all evaluation results into a final assessment."""
        print("STEP 4: Compiling final assessment...")
        validation_result = self.results_compiler.run({
            "paper_id": state["paper_id"],
            "paper_structure": state["paper_structure"],
            "step_evidence": state["step_evidence"],
            "figure_evaluations": state.get("figure_evaluations", []),
            "math_evaluations": state.get("math_evaluations", []),
            "citation_checks": state.get("citation_checks", []),
        })
        print(f"  Final confidence score: {validation_result.confidence_score:.2%}")

        # Save validation to database
        if state.get("save_to_db") and self.db:
            self.db.save_validation(validation_result, state["paper_id"])
            print("  Validation saved to database")

        return {"validation_result": validation_result}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, paper_id: str, paper_folder: Path, save_to_db: bool = True,
            bibliography: Dict[str, str] = None) -> ValidationResult:
        """
        Run the complete validation pipeline on a paper.

        Args:
            paper_id: Unique identifier for the paper
            paper_folder: Path to the folder containing the paper's LaTeX and images
            save_to_db: Whether to save to database
            bibliography: Dict of citation references

        Returns:
            ValidationResult with complete assessment
        """
        print(f"\n{'='*60}")
        print(f"Running validation pipeline")
        print(f"Paper ID: {paper_id}")
        print(f"{'='*60}\n")

        initial_state: PipelineState = {
            "paper_id": paper_id,
            "paper_folder": paper_folder,
            "save_to_db": save_to_db,
            "bibliography": bibliography or {},
        }

        final_state = self._graph.invoke(initial_state)

        print(f"\n{'='*60}")
        print("Pipeline complete!")
        print(f"{'='*60}\n")

        return final_state["validation_result"]

    def load_from_database(self, paper_id: str) -> Optional[ValidationResult]:
        """Load the latest validation for a paper from database."""
        if not self.db:
            raise ValueError("Database not initialized")

        return self.db.get_latest_validation(paper_id)

    def __del__(self):
        """Cleanup on deletion."""
        if self.db:
            self.db.disconnect()
