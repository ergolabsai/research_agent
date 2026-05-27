# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Validation pipeline contracts.

Ported from advisor_pipeline/models/schemas.py during MIGRATION step 2.
The shape of `ValidationResult.overall_assessment` is slated to become fully
structured per capabilities/validation/0005; that change lands separately.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from core.contracts.jobs import JobId
from core.contracts.paper import Paper


# ---- Use-case I/O ----------------------------------------------------------


class ValidatePaperRequest(BaseModel):
    paper: Paper

    model_config = {"frozen": True}


class ValidatePaperResponse(BaseModel):
    job_id: JobId

    model_config = {"frozen": True}


# ---- Pipeline-internal types (consumed by the orchestrator and surfaced in the result)


class LogicalStep(BaseModel):
    """A single logical step in the paper's argument."""

    step_number: int = Field(description="Order of this step in the logical chain")
    description: str = Field(description="What this step claims or establishes")
    depends_on: list[int] = Field(
        description="Which previous steps this depends on", default_factory=list
    )
    section: str = Field(description="Which section of the paper this appears in")


class PaperStructure(BaseModel):
    """Output from the map_logic step: title, main claim, and logical steps."""

    title: str
    main_claim: str
    logical_steps: list[LogicalStep]


class Evidence(BaseModel):
    """Generic evidence supporting a logical step."""

    evidence_type: str = Field(description="Type: 'figure', 'math', or 'citation'")
    description: str
    location: str = Field(
        description=(
            "Where in the paper (section, page, figure number). For figures, must be the "
            "exact filename from the submitted figure list."
        )
    )
    supports_step: int
    excerpt: str = Field(
        default="",
        description="Short verbatim quote from the paper text supporting this evidence item.",
    )


class StepEvidence(BaseModel):
    step_number: int = Field(default=0)
    evidence_list: list[Evidence] = Field(default_factory=list)


class Comparison(BaseModel):
    differences: list[str] = Field(default_factory=list)
    similarities: list[str] = Field(default_factory=list)


class ClaimValidity(BaseModel):
    confirmations: list[str] = Field(
        description="Items that support the validity of the supporting statement."
    )
    contradictions: list[str] = Field(
        description="Items that undermine the validity of the supporting statement."
    )


class FigureClaimAssessment(BaseModel):
    supports_step: int
    claim: str
    validity: ClaimValidity


class FigureEvaluation(BaseModel):
    figure_name: str
    actual_description: str = Field(description="What the figure actually shows (from vision).")
    expected_description: str = Field(
        description="What the figure should show based on the paper text alone."
    )
    comparison: Comparison
    claim_assessments: list[FigureClaimAssessment] = Field(default_factory=list)


class MathEvaluation(BaseModel):
    equation_reference: str
    supports_step: int
    calculation_valid: bool
    details: str
    formula_used: str | None = None


class RelatedPaper(BaseModel):
    paper_id: str = Field(description="arXiv ID, DOI, or Semantic Scholar ID")
    title: str
    authors: str
    abstract: str
    source: str = Field(
        description="How this paper was found: 'lancedb_fts', 'lancedb_vector', or 'semantic_scholar'."
    )
    relevancy_score: float = Field(ge=0.0, le=1.0, default=0.0)
    relevancy_reasoning: str = ""
    convergence_score: float = Field(
        ge=-1.0,
        le=1.0,
        default=0.0,
        description="Positive: conclusions agree. Negative: conclusions contradict.",
    )
    convergence_reasoning: str = ""


class OverallAssessment(BaseModel):
    """Final assessment prose.

    Currently a single markdown string in `review`. Per capabilities/validation/0005
    (proposed), this becomes structured fields (summary, strengths, weaknesses,
    recommendations). Keeping the legacy field for now; the contract evolves with the ADR.
    """

    review: str


class ValidationResult(BaseModel):
    """Final compiled output of the validation pipeline."""

    paper_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    paper_structure: PaperStructure
    # Step-keyed validation payloads. Schema varies per evidence type; left as Any
    # pending the structured-output rework (validation/0005).
    step_validations: dict[int, dict[str, Any]]
    overall_assessment: OverallAssessment
    confidence_score: float = Field(ge=0.0, le=1.0)
