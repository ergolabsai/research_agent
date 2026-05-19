# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Figure evaluator — evaluates whether figures support the claims made about them.

4-stage evaluation per figure:
1. Describe what the figure actually shows (vision)
2. Describe what it should show based on text alone
3. Compare similarities and differences
4. Assess each associated claim based on the comparison
"""

from typing import Dict, List

from advisor_pipeline.llm import get_structured_output, invoke_text, invoke_vision
from advisor_pipeline.mcp_servers.advisor_server.prompts import (
    CLAIM_ASSESSOR,
    FIGURE_COMPARATOR,
    FIGURE_DESCRIBER,
    FIGURE_EXPECTED,
)
from advisor_pipeline.models.schemas import (
    Comparison,
    FigureClaimAssessment,
    FigureEvaluation,
)


class FigureEvaluator:
    """Evaluates figure-based evidence without BaseAgent inheritance."""

    def run(
        self,
        figures: Dict[str, Dict[str, str]],
        figure_claims: Dict[str, List[Dict]],
        paper_text: str,
    ) -> List[FigureEvaluation]:
        """Evaluate all figures.

        Args:
            figures: Dict mapping figure names to {'data': base64_str, 'media_type': str}.
            figure_claims: Dict mapping figure names to list of
                {'supports_step': int, 'claim': str}.
            paper_text: Full paper text.

        Returns:
            List of FigureEvaluation objects.
        """
        if not figures:
            print("No figures to evaluate")
            return []

        evaluations = []

        for figure_name, figure_data in figures.items():
            print(f"Evaluating figure: {figure_name}")

            # Step A: Describe what the figure actually shows (vision)
            actual_description = self._describe_figure(
                figure_data["media_type"],
                figure_data["data"],
            )
            print("  Actual description complete")

            # Step B: Describe what it should show based on text
            expected_description = self._describe_expected(figure_name, paper_text)
            print("  Expected description complete")

            # Step C: Compare
            comparison = self._compare_descriptions(actual_description, expected_description)
            print(
                f"  Comparison complete: {len(comparison.similarities)} similarities, "
                f"{len(comparison.differences)} differences"
            )

            # Step D: Assess each claim
            claims = figure_claims.get(figure_name, [])
            claim_assessments = []
            for claim_info in claims:
                assessment = self._assess_claim(
                    figure_name,
                    actual_description,
                    expected_description,
                    comparison,
                    claim_info["claim"],
                    claim_info["supports_step"],
                    paper_text,
                )
                claim_assessments.append(assessment)
            print(f"  Assessed {len(claim_assessments)} claims")

            evaluations.append(
                FigureEvaluation(
                    figure_name=figure_name,
                    actual_description=actual_description,
                    expected_description=expected_description,
                    comparison=comparison,
                    claim_assessments=claim_assessments,
                )
            )

        return evaluations

    def _describe_figure(self, media_type: str, image_data: str) -> str:
        return invoke_vision(FIGURE_DESCRIBER, media_type, image_data)

    def _describe_expected(self, figure_name: str, paper_text: str) -> str:
        return invoke_text(FIGURE_EXPECTED.format(figure_name=figure_name, paper_text=paper_text))

    def _compare_descriptions(self, actual: str, expected: str) -> Comparison:
        return get_structured_output(
            Comparison,
            FIGURE_COMPARATOR.format(actual_description=actual, expected_description=expected),
        )

    def _assess_claim(
        self,
        figure_name: str,
        actual: str,
        expected: str,
        comparison: Comparison,
        claim: str,
        supports_step: int,
        paper_text: str,
    ) -> FigureClaimAssessment:
        similarities = "\n".join(f"- {s}" for s in comparison.similarities)
        differences = "\n".join(f"- {d}" for d in comparison.differences)

        return get_structured_output(
            FigureClaimAssessment,
            CLAIM_ASSESSOR.format(
                figure_name=figure_name,
                supports_step=supports_step,
                claim=claim,
                actual_description=actual,
                expected_description=expected,
                similarities=similarities,
                differences=differences,
                paper_text=paper_text,
            ),
        )
