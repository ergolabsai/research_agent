from pydantic import BaseModel, Field
from typing import Dict

class FigureDescription(BaseModel):
    description: str = Field(description="description of the image")


class ExpectedFigureDescription(BaseModel):
    description: str = Field(description="expected figure description")


class FigureDifferences(BaseModel):
    differences: list[str] = Field(
        description="A list where each item is one distinct difference between the descriptions"
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
    validity: str = Field(description="how does the validity change")
