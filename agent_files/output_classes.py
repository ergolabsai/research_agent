from pydantic import BaseModel, Field
from typing import Dict, List

class ContextString(BaseModel):
    context: str = Field(description="context for future API calls")


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


class SupportingClaim(BaseModel):
    """A supporting claim with evidence from a figure."""
    description: str = Field(description="3-4 sentence description of the claim")
    figures: list[FigureInfo] = Field(description="The figure(s) supporting this claim")


class ResearchAnalysis(BaseModel):
    """Main research analysis structure with question, answer, and supporting claims."""
    question: str = Field(description="The main question in 2-3 sentences")
    answer: str = Field(description="The author's answer")
    supporting_claims: Dict[str, SupportingClaim] = Field(
        description="Dictionary of supporting claims where keys are importance scores (e.g., '1', '2', 'n' where 'n' is the number of supporting claims)"
    )


class ClaimValidity(BaseModel):
    confirmations: list[str] = Field(
        description="A list of confirmations that support the the validity of the supporting statement."
    )
    contradictions: list[str] = Field(
        description="A list of differences that undermine the the validity of the supporting statement."
    )


class OverAllReview(BaseModel):
    review: str = Field(description="Review of the paper")
