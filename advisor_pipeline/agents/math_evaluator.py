# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Math evaluator — validates mathematical evidence using MCP calculator tools.

Uses a LangGraph ReAct agent with calculator tools, then structures
the result as MathEvaluation via get_structured_output().
"""

import json
import re
from typing import Dict, List

from langchain_core.messages import HumanMessage
from langchain_core.tools import StructuredTool, Tool
from langgraph.prebuilt import create_react_agent

from core.ports.calculator import Calculator
from core.ports.llm_client import LLMClient
from core.services.prompts import MATH_REPORTER, MATH_VERIFIER
from advisor_pipeline.models.schemas import Evidence, MathEvaluation


class MathEvaluator:
    """Validates mathematical evidence without BaseAgent inheritance.

    Uses a create_react_agent loop with 4 MCP calculator tools.
    """

    def __init__(self, llm: LLMClient, calculator: Calculator | None = None):
        self._llm = llm
        self.mcp_client = calculator
        self._tools = self._build_tools()
        self._agent = create_react_agent(self._llm.bind_tools(self._tools), self._tools)

    def _build_tools(self) -> list[Tool]:
        mcp_client = self.mcp_client

        def call_mcp_calculator(formula_name: str, known_values: str) -> str:
            """Calculate unknown variable given formula and known values (JSON)."""
            if not mcp_client:
                return "Error: MCP client not initialized"
            try:
                values = json.loads(known_values)
                result = mcp_client.call_tool(
                    "calculate", formula_name=formula_name, known_values=values
                )
                return json.dumps(result, indent=2)
            except json.JSONDecodeError:
                return f"Error: Invalid JSON: {known_values}"
            except Exception as e:
                return f"Error: {e}"

        def list_available_formulas() -> str:
            """List all available formulas in the calculator."""
            if not mcp_client:
                return "Error: MCP client not initialized"
            try:
                result = mcp_client.call_tool("list_formulas")
                return json.dumps(result, indent=2)
            except Exception as e:
                return f"Error: {e}"

        def describe_formula(formula_name: str) -> str:
            """Get details about a specific formula."""
            if not mcp_client:
                return "Error: MCP client not initialized"
            try:
                result = mcp_client.call_tool("describe_formula", formula_name=formula_name)
                return json.dumps(result, indent=2)
            except Exception as e:
                return f"Error: {e}"

        def verify_calculation(formula_name: str, all_values: str) -> str:
            """Verify that a set of values satisfies a formula (all values as JSON)."""
            if not mcp_client:
                return "Error: MCP client not initialized"
            try:
                values = json.loads(all_values)
                result = mcp_client.call_tool("verify", formula_name=formula_name, values=values)
                return json.dumps(result, indent=2)
            except Exception as e:
                return f"Error: {e}"

        return [
            StructuredTool.from_function(
                func=call_mcp_calculator,
                name="call_mcp_calculator",
                description=(
                    "Calculate unknown variable given formula and known values. "
                    "Provide formula_name and known_values as JSON string."
                ),
            ),
            StructuredTool.from_function(
                func=list_available_formulas,
                name="list_available_formulas",
                description="Get list of all available formulas in the calculator",
            ),
            StructuredTool.from_function(
                func=describe_formula,
                name="describe_formula",
                description=(
                    "Get detailed information about a specific formula including "
                    "variables and units"
                ),
            ),
            StructuredTool.from_function(
                func=verify_calculation,
                name="verify_calculation",
                description="Verify that a complete set of values satisfies a formula equation",
            ),
        ]

    def run(
        self,
        evidence_list: List[Evidence],
        paper_text: str,
        claims: Dict[int, str],
    ) -> List[MathEvaluation]:
        """Validate all mathematical evidence.

        Args:
            evidence_list: Evidence items (already filtered to math type).
            paper_text: Full paper text for context.
            claims: Dict mapping step numbers to claim descriptions.

        Returns:
            List of MathEvaluation objects.
        """
        math_evidence = [e for e in evidence_list if e.evidence_type == "math"]
        if not math_evidence:
            print("No math evidence to evaluate")
            return []

        evaluations = []

        for evidence in math_evidence:
            print(f"Evaluating math evidence: {evidence.location}")
            claim = claims.get(evidence.supports_step, "Unknown claim")
            equation_context = self._extract_equation_context(paper_text, evidence.location)

            # Run the agent
            agent_input = MATH_VERIFIER.format(
                equation_location=evidence.location,
                equation_description=evidence.description,
                claim=claim,
                equation_context=equation_context,
            )
            result = self._agent.invoke(
                {"messages": [HumanMessage(content=agent_input)]},
                {"recursion_limit": 10},
            )
            agent_result = result["messages"][-1].content if result.get("messages") else ""

            # Structure the result
            prompt = MATH_REPORTER.format(
                equation_location=evidence.location,
                equation_description=evidence.description,
                supports_step=evidence.supports_step,
                claim=claim,
                agent_result=agent_result,
            )
            evaluation = self._llm.get_structured_output(MathEvaluation, prompt)
            evaluations.append(evaluation)

        return evaluations

    @staticmethod
    def _extract_equation_context(
        paper_text: str, equation_ref: str, context_chars: int = 1000
    ) -> str:
        pattern = re.escape(equation_ref.replace("Eq.", "").replace("Equation", "").strip())
        pattern = f"(?:Eq|Equation).*?{pattern}"
        match = re.search(pattern, paper_text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - context_chars // 2)
            end = min(len(paper_text), match.end() + context_chars // 2)
            return paper_text[start:end]
        return paper_text[:context_chars]
