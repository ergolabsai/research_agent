# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""MathEvaluator unit tests against a fake LLMClient.

The react-agent itself is replaced with a stub on the instance — exercising
the real LangGraph loop belongs in an integration test. What we lock in here
is that the new constructor signature (`llm`, `calculator`) wires the LLM
port through `bind_tools` and `get_structured_output`, and that the run loop
emits one MathEvaluation per input evidence item.
"""

import advisor_pipeline.agents.math_evaluator as math_evaluator_mod
from advisor_pipeline.agents.math_evaluator import MathEvaluator
from advisor_pipeline.models.schemas import Evidence, MathEvaluation
from tests.services.conftest import FakeLLMClient


class _StubAgent:
    def invoke(self, _state, _cfg):
        return {"messages": [type("M", (), {"content": "agent verified ok"})()]}


def _patch_react_agent(monkeypatch):
    """Bypass create_react_agent's Runnable validation in __init__."""
    monkeypatch.setattr(
        math_evaluator_mod,
        "create_react_agent",
        lambda _model, _tools: _StubAgent(),
    )


def test_constructor_binds_tools_via_llm_port(monkeypatch):
    _patch_react_agent(monkeypatch)
    llm = FakeLLMClient()
    MathEvaluator(llm=llm, calculator=None)
    # The whole point of the port: bind_tools must go through the LLM seam,
    # not through `get_llm()` directly.
    assert len(llm.bind_tools_calls) == 1
    tools = llm.bind_tools_calls[0]
    tool_names = {t.name for t in tools}
    assert tool_names == {
        "call_mcp_calculator",
        "list_available_formulas",
        "describe_formula",
        "verify_calculation",
    }


def test_run_emits_one_evaluation_per_math_evidence(monkeypatch):
    _patch_react_agent(monkeypatch)
    llm = FakeLLMClient(
        structured_responses={
            "MathEvaluation": [
                MathEvaluation(
                    equation_reference="Eq. 1",
                    supports_step=1,
                    calculation_valid=True,
                    details="checks out",
                    formula_used="kinetic_energy",
                ),
            ],
        },
    )
    evaluator = MathEvaluator(llm=llm, calculator=None)

    out = evaluator.run(
        evidence_list=[
            Evidence(
                evidence_type="math",
                description="KE calculation",
                location="Eq. 1",
                supports_step=1,
            ),
            Evidence(
                evidence_type="citation",
                description="should be filtered out",
                location="ref [3]",
                supports_step=1,
            ),
        ],
        paper_text="paper body Eq. 1 ...",
        claims={1: "energy conserved"},
    )

    assert len(out) == 1
    assert out[0].equation_reference == "Eq. 1"
    assert out[0].calculation_valid is True
    # The LLM port saw exactly one structured-output call (the MathEvaluation report).
    assert len(llm.structured_calls) == 1


def test_run_returns_empty_when_no_math_evidence(monkeypatch):
    _patch_react_agent(monkeypatch)
    llm = FakeLLMClient()
    evaluator = MathEvaluator(llm=llm, calculator=None)

    out = evaluator.run(
        evidence_list=[
            Evidence(
                evidence_type="citation",
                description="x",
                location="y",
                supports_step=1,
            )
        ],
        paper_text="",
        claims={},
    )
    assert out == []
    assert llm.structured_calls == []
