from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

#### Context Agent
class ContextList(BaseModel):
    context: List[str] = Field(
        description="context for future API calls",
        default_factory=list)


class ContextString(BaseModel):
    context: str = Field(description="context for future API calls")


#### Logic Maping Agent
class LogicalStep(BaseModel):
    """A single logical step in the paper's argument."""
    step_number: int = Field(description="Order of this step in the logical chain")
    description: str = Field(description="What this step claims or establishes")
    depends_on: List[int] = Field(
        description="Which previous steps this depends on",
        default_factory=list
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
    evidence_type: str = Field(description="Type: 'figure', 'math', 'citation', or 'text'")
    description: str = Field(description="What this evidence shows")
    location: str = Field(description="Where in the paper (section, page, figure number, etc.)")
    supports_step: int = Field(description="Which logical step this supports")


class StepEvidence(BaseModel):
    """Output from Step 2: Evidence identification for each step."""
    evidence_list: List[Evidence] = Field(description="list of evidence to support a logical step", default_factory=list)


class FigureDescription(BaseModel):
    description: str = Field(description="description of the image")


class ExpectedFigureDescription(BaseModel):
    description: str = Field(description="expected figure description")


class Comparison(BaseModel):
    """Comparison results with differences and similarities."""
    differences: List[str] = Field(
        description="List of differences found",
        default_factory=list
    )
    similarities: List[str] = Field(
        description="List of similarities found",
        default_factory=list
    )


class FigureInfo(BaseModel):
    """Numerical evidence from a figure or source."""
    name: str = Field(description="name of the figure from the figure list")
    value: float = Field(description="The numerical value")
    units: str = Field(description="The units for the value")


class ClaimValidity(BaseModel):
    confirmations: list[str] = Field(
        description="A list of confirmations that support the the validity of the supporting statement."
    )
    contradictions: list[str] = Field(
        description="A list of differences that undermine the the validity of the supporting statement."
    )


class OverAllReview(BaseModel):
    review: str = Field(description="Review of the paper")


class FigureEvaluation(BaseModel):
    """Output from Step 3: Figure-based evidence evaluation."""
    figure_name: str = Field(description="Name/number of the figure")
    supports_step: int = Field(description="Which logical step this figure supports")
    extracted_data: List[FigureInfo] = Field(
        description="Numerical data extracted from figure",
        default_factory=list
    )
    validity: ClaimValidity = Field(description="Whether the figure supports the claim")
    notes: str = Field(description="Additional observations about the figure", default="")


class MathEvaluation(BaseModel):
    """Output from Step 4: Math-based evidence evaluation."""
    equation_reference: str = Field(description="Which equation (e.g., 'Eq. 3' or page number)")
    supports_step: int = Field(description="Which logical step this math supports")
    calculation_valid: bool = Field(description="Whether the math checks out")
    details: str = Field(description="Explanation of the validation or errors found")
    formula_used: Optional[str] = Field(description="Name of formula from MCP server", default=None)


class CitationCheck(BaseModel):
    """Output from Step 5: Citation verification."""
    citation: str = Field(description="The citation being checked")
    supports_step: int = Field(description="Which logical step this citation supports")
    accessible: bool = Field(description="Whether the citation could be accessed")
    supports_claim: Optional[bool] = Field(
        description="Whether citation actually supports the claim (None if not accessible)",
        default=None
    )
    notes: str = Field(description="Details about what the citation says", default="")


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
        description="0-1 score for overall confidence in the paper's claims",
        ge=0.0,
        le=1.0
    )


# ===== MongoDB Document Models =====

class PaperDocument(BaseModel):
    """MongoDB document for storing paper metadata and content."""
    paper_id: str = Field(description="Unique identifier")
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str = Field(default="")
    full_text: str = Field(description="Full paper text")
    figures: Dict[str, str] = Field(
        description="Figure name to file path mapping",
        default_factory=dict
    )
    created_at: datetime = Field(default_factory=datetime.now)


class ValidationDocument(BaseModel):
    """MongoDB document for storing validation results."""
    paper_id: str
    validation_result: ValidationResult
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
