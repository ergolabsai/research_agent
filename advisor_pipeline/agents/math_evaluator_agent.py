from typing import Any, Dict, List
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate
import json

from advisor_pipeline.agents.base_agent import BaseAgent
from advisor_pipeline.models.schemas import Evidence, MathEvaluation


class MathEvaluatorAgent(BaseAgent):
    """
    Agent responsible for validating mathematical evidence.
    Uses MCP calculator server to verify calculations.
    
    Input: List of math evidence
    Output: List of MathEvaluation
    """
    
    def __init__(self, mcp_client=None):
        super().__init__(
            name="MathEvaluator",
            description="Validates mathematical derivations and calculations"
        )
        
        # Store MCP client for calculator access
        self.mcp_client = mcp_client
        
        self.tools = self.get_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a mathematical verification specialist. For each equation or calculation:
1. Identify what formula or physical law is being applied
2. Extract the input values and their units
3. Determine what the expected output should be
4. Use the MCP calculator to verify the math
5. Check unit consistency

Be rigorous - even small errors matter in scientific papers."""),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        self.initialize_agent(prompt)
    
    def get_tools(self):
        """Define tools for mathematical validation."""
        
        def call_mcp_calculator(formula_name: str, known_values: str) -> str:
            """
            Call MCP calculator server to verify a calculation.
            
            Args:
                formula_name: Name of the formula (e.g., 'wave_equation')
                known_values: JSON string of known values (e.g., '{"speed": 340, "frequency": 500}')
            
            Returns:
                Calculation result or error message
            """
            if not self.mcp_client:
                return "Error: MCP client not initialized"
            
            try:
                values = json.loads(known_values)
                # Call your existing MCP calculator
                result = self.mcp_client.call_tool(
                    "calculate",
                    formula_name=formula_name,
                    known_values=values
                )
                return json.dumps(result, indent=2)
            except json.JSONDecodeError:
                return f"Error: Invalid JSON for known_values: {known_values}"
            except Exception as e:
                return f"Error calling MCP calculator: {str(e)}"
        
        def list_available_formulas() -> str:
            """List all formulas available in MCP calculator."""
            if not self.mcp_client:
                return "Error: MCP client not initialized"
            
            try:
                result = self.mcp_client.call_tool("list_formulas")
                return json.dumps(result, indent=2)
            except Exception as e:
                return f"Error listing formulas: {str(e)}"
        
        def describe_formula(formula_name: str) -> str:
            """Get details about a specific formula."""
            if not self.mcp_client:
                return "Error: MCP client not initialized"
            
            try:
                result = self.mcp_client.call_tool(
                    "describe_formula",
                    formula_name=formula_name
                )
                return json.dumps(result, indent=2)
            except Exception as e:
                return f"Error describing formula: {str(e)}"
        
        def verify_calculation(formula_name: str, all_values: str) -> str:
            """
            Verify that a set of values satisfies a formula.
            
            Args:
                formula_name: Name of the formula
                all_values: JSON string with ALL variable values
            """
            if not self.mcp_client:
                return "Error: MCP client not initialized"
            
            try:
                values = json.loads(all_values)
                result = self.mcp_client.call_tool(
                    "verify",
                    formula_name=formula_name,
                    values=values
                )
                return json.dumps(result, indent=2)
            except Exception as e:
                return f"Error verifying calculation: {str(e)}"
        
        return [
            Tool(
                name="call_mcp_calculator",
                func=call_mcp_calculator,
                description="Calculate unknown variable given formula and known values. Provide formula_name and known_values as JSON."
            ),
            Tool(
                name="list_available_formulas",
                func=list_available_formulas,
                description="Get list of all available formulas in the calculator"
            ),
            Tool(
                name="describe_formula",
                func=describe_formula,
                description="Get detailed information about a specific formula including variables and units"
            ),
            Tool(
                name="verify_calculation",
                func=verify_calculation,
                description="Verify that a complete set of values satisfies a formula equation"
            )
        ]
    
    def run(self, input_data: Dict[str, Any]) -> List[MathEvaluation]:
        """
        Validate all mathematical evidence.
        
        Args:
            input_data: Must contain:
                - 'evidence_list': List[Evidence] filtered to math evidence
                - 'paper_text': Full paper text for context
                - 'claims': Dict mapping step numbers to claims
                
        Returns:
            List of MathEvaluation objects
        """
        evidence_list: List[Evidence] = input_data.get("evidence_list", [])
        paper_text: str = input_data.get("paper_text", "")
        claims: Dict[int, str] = input_data.get("claims", {})
        
        # Filter to only math evidence
        math_evidence = [e for e in evidence_list if e.evidence_type == "math"]
        
        if not math_evidence:
            print("No math evidence to evaluate")
            return []
        
        evaluations = []
        
        for evidence in math_evidence:
            print(f"Evaluating math evidence: {evidence.location}")
            
            # Get the claim this equation supports
            claim = claims.get(evidence.supports_step, "Unknown claim")
            
            # Extract equation context from paper
            equation_context = self._extract_equation_context(
                paper_text,
                evidence.location
            )
            
            # Use agent to identify formula and extract values
            agent_input = f"""Analyze this mathematical evidence:

Equation reference: {evidence.location}
Purpose: {evidence.description}
Supporting claim: {claim}

Context from paper:
{equation_context}

Tasks:
1. First, list available formulas to see what's in the calculator
2. Identify which formula matches this equation
3. Extract the numerical values and units from the paper
4. Use the calculator to verify the math
"""
            
            agent_result = self.agent_executor.invoke({"input": agent_input})
            
            # Use Instructor to structure the validation result
            prompt = f"""Create a mathematical validation report:

Equation: {evidence.location}
Context: {evidence.description}
Supports step {evidence.supports_step}: {claim}

Agent verification:
{agent_result.get('output', '')}

Based on the agent's work with the MCP calculator, determine:
1. Whether the calculation is valid
2. What formula was used (if applicable)
3. Detailed explanation of findings
"""
            
            evaluation = self.get_structured_output(
                prompt=prompt,
                response_model=MathEvaluation,
                context={
                    "equation_reference": evidence.location,
                    "supports_step": evidence.supports_step
                }
            )
            
            evaluations.append(evaluation)
        
        return evaluations
    
    def _extract_equation_context(self, paper_text: str, equation_ref: str, 
                                   context_chars: int = 1000) -> str:
        """Extract text around an equation reference."""
        import re
        
        # Try to find the equation reference in the paper
        # Look for patterns like "Eq. 3", "Equation (3)", etc.
        pattern = re.escape(equation_ref.replace("Eq.", "").replace("Equation", "").strip())
        pattern = f"(?:Eq|Equation).*?{pattern}"
        
        match = re.search(pattern, paper_text, re.IGNORECASE)
        
        if match:
            start = max(0, match.start() - context_chars // 2)
            end = min(len(paper_text), match.end() + context_chars // 2)
            return paper_text[start:end]
        
        # Fallback: just return some text (improve this with better parsing)
        return paper_text[:context_chars]
