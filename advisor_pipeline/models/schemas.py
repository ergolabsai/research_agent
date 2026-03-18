from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


#### Context Agent
class ContextList(BaseModel):
    context: List[str] = Field(description="context for future API calls", default_factory=list)


class ContextString(BaseModel):
    context: str = Field(description="context for future API calls")


#### Logic Maping Agent
class LogicalStep(BaseModel):
    """A single logical step in the paper's argument."""

    step_number: int = Field(description="Order of this step in the logical chain")
    description: str = Field(description="What this step claims or establishes")
    depends_on: List[int] = Field(
        description="Which previous steps this depends on", default_factory=list
    )
    section: str = Field(description="Which section of the paper this appears in")


class PaperStructure(BaseModel):
    """Output from Step 1: Paper reading and logical step identification."""

    title: str = Field(description="Paper title")
    main_claim: str = Field(description="The paper's primary claim or thesis")
    logical_steps: List[LogicalStep] = Field(description="Ordered list of logical steps")


#### Evidence Finder Agent
class Evidence(BaseModel):
    """Generic evidence supporting a logical step."""

    evidence_type: str = Field(description="Type: 'figure', 'math', or 'citation'")
    description: str = Field(description="What this evidence shows")
    location: str = Field(
        description=(
        "Where in the paper (section, page, figure number, etc.) "
        "If the evidence_type is 'figure', this MUST be the exact "
        "filename from the available figure files list."
    )
    )
    supports_step: int = Field(description="Which logical step this supports")
    excerpt: str = Field(
        description=(
            "A short direct quote from the paper text that supports this evidence item. "
            "Should be copied verbatim from the paper."
        ),
        default="",
    )


class StepEvidence(BaseModel):
    """Output from Step 2: Evidence identification for each step."""

    step_number: int = Field(default=0, description="Which logical step this evidence belongs to")
    evidence_list: List[Evidence] = Field(
        description="list of evidence to support a logical step", default_factory=list
    )


#### Figure Evaluator Agent
class Comparison(BaseModel):
    """Comparison results with differences and similarities."""

    differences: List[str] = Field(description="List of differences found", default_factory=list)
    similarities: List[str] = Field(description="List of similarities found", default_factory=list)


class FigureInfo(BaseModel):
    """Numerical evidence from a figure or source."""

    name: str = Field(description="name of the figure from the figure list")
    value: float = Field(description="The numerical value")
    units: str = Field(description="The units for the value")


class ClaimValidity(BaseModel):
    confirmations: list[str] = Field(
        description="A list of confirmations that support the validity of the supporting statement."
    )
    contradictions: list[str] = Field(
        description="A list of differences that undermine the validity of the supporting statement."
    )


class OverAllReview(BaseModel):
    review: str = Field(description="Review of the paper")


class FigureClaimAssessment(BaseModel):
    """Assessment of a single claim against a figure's comparison results."""

    supports_step: int = Field(description="Which logical step this claim belongs to")
    claim: str = Field(description="The claim being assessed")
    validity: ClaimValidity = Field(
        description="Confirmations and contradictions for this claim based on figure comparison"
    )


class FigureEvaluation(BaseModel):
    """Output from Step 3: Figure-based evidence evaluation."""

    figure_name: str = Field(description="Name/number of the figure")
    actual_description: str = Field(
        description="Description of what the figure actually shows (from vision)"
    )
    expected_description: str = Field(
        description="Description of what the figure should show based on the paper text alone"
    )
    comparison: Comparison = Field(
        description="Similarities and differences between actual and expected descriptions"
    )
    claim_assessments: List[FigureClaimAssessment] = Field(
        description="Assessment of each claim associated with this figure", default_factory=list
    )


class MathEvaluation(BaseModel):
    """Output from Step 4: Math-based evidence evaluation."""

    equation_reference: str = Field(description="Which equation (e.g., 'Eq. 3' or page number)")
    supports_step: int = Field(description="Which logical step this math supports")
    calculation_valid: bool = Field(description="Whether the math checks out")
    details: str = Field(description="Explanation of the validation or errors found")
    formula_used: Optional[str] = Field(description="Name of formula from MCP server", default=None)


class RelatedPaper(BaseModel):
    """A paper found by the Librarian, scored for relevancy and convergence."""

    paper_id: str = Field(description="arXiv ID, DOI, or Semantic Scholar ID")
    title: str = Field(description="Title of the related paper")
    authors: str = Field(description="Author list as a single string")
    abstract: str = Field(description="Abstract of the related paper")
    source: str = Field(
        description="How this paper was found: 'lancedb_fts', 'lancedb_vector', or 'semantic_scholar'"
    )
    relevancy_score: float = Field(
        description="0.0–1.0 indicating how important this paper is for evaluating the user's paper",
        ge=0.0,
        le=1.0,
        default=0.0,
    )
    relevancy_reasoning: str = Field(
        description="Why this relevancy score was assigned", default=""
    )
    convergence_score: float = Field(
        description=(
            "-1.0 to +1.0 indicating alignment of conclusions. "
            "Positive = conclusions agree, Negative = conclusions contradict"
        ),
        ge=-1.0,
        le=1.0,
        default=0.0,
    )
    convergence_reasoning: str = Field(
        description="Why this convergence score was assigned", default=""
    )


class RelatedPaperScored(BaseModel):
    """LLM-produced relevancy + convergence scores for a single related paper."""

    relevancy_score: float = Field(
        description="0.0–1.0 indicating how important this paper is for evaluating the user's paper",
        ge=0.0,
        le=1.0,
    )
    relevancy_reasoning: str = Field(description="Why this relevancy score was assigned")
    convergence_score: float = Field(
        description=(
            "-1.0 to +1.0 indicating alignment of conclusions. "
            "Positive = conclusions agree, Negative = conclusions contradict"
        ),
        ge=-1.0,
        le=1.0,
    )
    convergence_reasoning: str = Field(description="Why this convergence score was assigned")


class LibrarianResult(BaseModel):
    """Output of the Librarian agent — related papers with scores."""

    related_papers: List[RelatedPaper] = Field(
        description="Papers found and scored by the Librarian", default_factory=list
    )
    context_summary: str = Field(
        description="Context summary derived from the related papers", default=""
    )
    search_queries: List[str] = Field(
        description="The vector search queries crafted by the LLM", default_factory=list
    )


class SearchQueries(BaseModel):
    """LLM-generated search queries for finding related papers via vector search."""

    queries: List[str] = Field(
        description=(
            "3-5 diverse, high-quality search queries to find related papers. "
            "Each should target a different aspect of the paper (methodology, "
            "domain, specific techniques, theoretical foundations, etc.)"
        )
    )


class ValidationResult(BaseModel):
    """Final compiled results from Step 6."""

    paper_id: str = Field(description="Unique identifier for the paper")
    timestamp: datetime = Field(default_factory=datetime.now)
    paper_structure: PaperStructure
    step_validations: Dict[int, Dict[str, Any]] = Field(
        description="For each logical step, validation results by evidence type"
    )
    overall_assessment: OverAllReview
    confidence_score: float = Field(
        description="0-1 score for overall confidence in the paper's claims", ge=0.0, le=1.0
    )
