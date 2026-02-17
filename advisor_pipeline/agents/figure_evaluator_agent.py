from typing import Any, Dict, List
from anthropic import Anthropic

from advisor_pipeline.agents.base_agent import BaseAgent
from advisor_pipeline.config.settings import settings
from advisor_pipeline.models.schemas import (
    FigureEvaluation,
    FigureClaimAssessment,
    FigureDescription,
    ExpectedFigureDescription,
    Comparison,
    ClaimValidity,
)


class FigureEvaluatorAgent(BaseAgent):
    """
    Agent responsible for evaluating figure-based evidence.

    For each figure:
    1. Describe what the figure actually shows (vision)
    2. Describe what the figure should show based on the paper text alone
    3. Compare similarities and differences
    4. Assess each associated claim based on the comparison

    Input: Pre-loaded figures (base64), figure-to-claims mapping, and paper text
    Output: List of FigureEvaluation
    """

    def __init__(self):
        super().__init__(
            name="FigureEvaluator",
            description="Evaluates whether figures actually support the claims made about them"
        )

        self.initialize_agent()

    def get_tools(self):
        return []

    def run(self, input_data: Dict[str, Any]) -> List[FigureEvaluation]:
        """
        Evaluate all figures.

        Args:
            input_data: Must contain:
                - 'figures': Dict mapping figure names to {'data': base64_str, 'media_type': str}
                - 'figure_claims': Dict mapping figure names to list of {'supports_step': int, 'claim': str}
                - 'paper_text': Full paper text

        Returns:
            List of FigureEvaluation objects
        """
        figures: Dict[str, Dict[str, str]] = input_data.get("figures", {})
        figure_claims: Dict[str, List[Dict]] = input_data.get("figure_claims", {})
        paper_text: str = input_data.get("paper_text", "")

        if not figures:
            print("No figures to evaluate")
            return []

        evaluations = []

        for figure_name, figure_data in figures.items():
            print(f"Evaluating figure: {figure_name}")

            # Step A: Describe what the figure actually shows using vision
            actual_description = self._describe_figure(
                figure_data['media_type'],
                figure_data['data'],
                figure_name
            )
            print(f"  Actual description complete")

            # Step B: Describe what the figure should look like based on text only
            expected_description = self._describe_expected(figure_name, paper_text)
            print(f"  Expected description complete")

            # Step C: Compare similarities and differences
            comparison = self._compare_descriptions(
                figure_name, actual_description, expected_description
            )
            print(f"  Comparison complete: {len(comparison.similarities)} similarities, {len(comparison.differences)} differences")

            # Step D: Assess each claim associated with this figure
            claims = figure_claims.get(figure_name, [])
            claim_assessments = []
            for claim_info in claims:
                assessment = self._assess_claim(
                    figure_name,
                    actual_description,
                    expected_description,
                    comparison,
                    claim_info['claim'],
                    claim_info['supports_step']
                )
                claim_assessments.append(assessment)
            print(f"  Assessed {len(claim_assessments)} claims")

            evaluation = FigureEvaluation(
                figure_name=figure_name,
                actual_description=actual_description,
                expected_description=expected_description,
                comparison=comparison,
                claim_assessments=claim_assessments
            )
            evaluations.append(evaluation)

        return evaluations

    def _describe_figure(self, media_type: str, image_data: str, figure_name: str) -> str:
        """Use Claude's vision to describe what the figure actually shows."""
        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.model_name,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": image_data},
                        },
                        {
                            "type": "text",
                            "text": f"""Describe this scientific figure ({figure_name}) in detail.

Include:
1. The type of figure (plot, diagram, photograph, schematic, etc.)
2. Axes labels and ranges (if applicable)
3. Data trends, patterns, and key features
4. Any specific numerical values visible
5. Legends, annotations, or labels

Be precise and objective. Only describe what you can actually see.""",
                        },
                    ],
                }
            ],
        )

        result = self.get_structured_output(
            prompt=f"""Format this vision analysis into a concise figure description:

{response.content[0].text}""",
            response_model=FigureDescription
        )
        return result.description

    def _describe_expected(self, figure_name: str, paper_text: str) -> str:
        """Based on the paper text alone, describe what this figure should show."""
        result = self.get_structured_output(
            prompt=f"""Based ONLY on the paper text below, describe what the figure "{figure_name}" should show.
Do NOT guess or infer beyond what the text explicitly states about this figure.
Include any specific values, trends, or features the text mentions about this figure.

Paper text:
{paper_text}""",
            response_model=ExpectedFigureDescription
        )
        return result.description

    def _compare_descriptions(
        self, figure_name: str, actual: str, expected: str
    ) -> Comparison:
        """Compare the actual and expected descriptions to find similarities and differences."""
        return self.get_structured_output(
            prompt=f"""Compare these two descriptions of figure "{figure_name}".

ACTUAL (from looking at the figure):
{actual}

EXPECTED (from the paper text):
{expected}

List the similarities (things that match between actual and expected) and
differences (things that don't match, are missing, or are unexpected).
Be specific and reference concrete details from both descriptions.""",
            response_model=Comparison
        )

    def _assess_claim(
        self,
        figure_name: str,
        actual: str,
        expected: str,
        comparison: Comparison,
        claim: str,
        supports_step: int
    ) -> FigureClaimAssessment:
        """Assess whether a specific claim is supported based on the figure comparison."""
        return self.get_structured_output(
            prompt=f"""Assess whether the following claim is supported by figure "{figure_name}",
given the comparison between what the figure actually shows and what was expected.

Claim (step {supports_step}): {claim}

Actual figure description: {actual}
Expected figure description: {expected}

Similarities found:
{chr(10).join(f"- {s}" for s in comparison.similarities)}

Differences found:
{chr(10).join(f"- {d}" for d in comparison.differences)}

Based on the comparison above, list:
- Confirmations: specific ways the figure supports this claim
- Contradictions: specific ways the figure undermines or fails to support this claim""",
            response_model=FigureClaimAssessment,
            context={"supports_step": supports_step, "claim": claim}
        )