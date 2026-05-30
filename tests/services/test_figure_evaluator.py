# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""FigureEvaluator unit tests against a fake LLMClient."""

from advisor_pipeline.agents.figure_evaluator import FigureEvaluator
from advisor_pipeline.models.schemas import (
    ClaimValidity,
    Comparison,
    FigureClaimAssessment,
)
from tests.services.conftest import FakeLLMClient


def test_run_walks_describe_compare_assess_for_each_figure():
    llm = FakeLLMClient(
        structured_responses={
            "Comparison": [
                Comparison(similarities=["axes labelled"], differences=["legend missing"])
            ],
            "FigureClaimAssessment": [
                FigureClaimAssessment(
                    supports_step=1,
                    claim="trend matches",
                    validity=ClaimValidity(
                        confirmations=["slope positive in both"],
                        contradictions=[],
                    ),
                ),
            ],
        },
        text_responses=["expected: a positive-slope line"],
        vision_responses=["actual: scatter with positive slope"],
    )

    evaluator = FigureEvaluator(llm=llm)
    figures = {
        "fig1.png": {"data": "<base64>", "media_type": "image/png"},
    }
    claims = {"fig1.png": [{"supports_step": 1, "claim": "trend matches"}]}

    out = evaluator.run(figures=figures, figure_claims=claims, paper_text="paper body")

    assert len(out) == 1
    eval0 = out[0]
    assert eval0.figure_name == "fig1.png"
    assert eval0.actual_description == "actual: scatter with positive slope"
    assert eval0.expected_description == "expected: a positive-slope line"
    assert eval0.comparison.similarities == ["axes labelled"]
    assert eval0.claim_assessments[0].validity.confirmations == ["slope positive in both"]

    # The seam: confirm each port method was called the expected number of times
    assert len(llm.vision_calls) == 1  # actual figure description
    assert len(llm.text_calls) == 1  # expected-from-text description
    assert len(llm.structured_calls) == 2  # Comparison + FigureClaimAssessment


def test_predicted_image_skips_text_expected_path():
    llm = FakeLLMClient(
        structured_responses={
            "Comparison": [Comparison(similarities=[], differences=[])],
        },
        vision_responses=["actual desc", "expected desc from predicted image"],
    )

    evaluator = FigureEvaluator(llm=llm)
    figures = {
        "fig1.png": {
            "data": "<actual-b64>",
            "media_type": "image/png",
            "predicted_data": "<predicted-b64>",
            "predicted_media_type": "image/png",
        }
    }

    evaluator.run(figures=figures, figure_claims={"fig1.png": []}, paper_text="ignored")

    assert len(llm.vision_calls) == 2  # actual + predicted (no text fallback)
    assert len(llm.text_calls) == 0


def test_empty_figures_returns_empty_without_llm_calls():
    llm = FakeLLMClient()
    evaluator = FigureEvaluator(llm=llm)

    assert evaluator.run(figures={}, figure_claims={}, paper_text="") == []
    assert llm.vision_calls == []
    assert llm.text_calls == []
    assert llm.structured_calls == []
