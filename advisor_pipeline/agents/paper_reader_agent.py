from typing import Any, Dict
from langchain_core.tools import Tool

from advisor_pipeline.agents.base_agent import BaseAgent
from advisor_pipeline.models.schemas import PaperStructure, LogicalStep


class PaperReaderAgent(BaseAgent):
    """
    Agent responsible for reading the paper and identifying key logical steps.

    Input: Full paper text
    Output: PaperStructure with ordered logical steps
    """

    def __init__(self):
        super().__init__(
            name="PaperReader",
            description="Reads scientific papers and extracts the logical argument structure"
        )
        self.tools = self.get_tools()

        # Initialize the agent with its system prompt
        system_prompt = """You are a scientific paper analyst. Your job is to:
1. Identify the paper's main claim or thesis
2. Break down the argument into discrete logical steps
3. Identify dependencies between steps (which steps build on which)
4. Note which section each step appears in

Be precise and capture the logical flow of the argument, not just a summary."""

        self.initialize_agent(system_prompt)
    
    def get_tools(self):
        """Define tools for paper analysis."""
        
        def extract_sections(text: str) -> str:
            """Extract section headers and their locations from paper text."""
            # Simple heuristic: look for common section patterns
            import re
            sections = re.findall(r'^(#+\s+.*|\d+\.?\s+[A-Z][^\n]+)$', text, re.MULTILINE)
            return "\n".join(sections[:20])  # Return first 20 sections
        
        def extract_main_equations(text: str) -> str:
            """Extract numbered equations from the paper."""
            import re
            # Look for equation markers like (1), Eq. 1, etc.
            equations = re.findall(r'(?:Eq\.|Equation)\s*\(?(\d+)\)?|\\begin{equation}.*?\\end{equation}', text, re.DOTALL)
            return f"Found {len(equations)} numbered equations"
        
        return [
            Tool(
                name="extract_sections",
                func=extract_sections,
                description="Extract section headers to understand paper structure"
            ),
            Tool(
                name="extract_main_equations", 
                func=extract_main_equations,
                description="Identify numbered equations in the paper"
            )
        ]
    
    def run(self, input_data: Dict[str, Any]) -> PaperStructure:
        """
        Read the paper and extract logical structure.

        Args:
            input_data: Must contain 'paper_text' and 'title'

        Returns:
            PaperStructure with identified logical steps
        """
        paper_text = input_data.get("paper_text", "")
        title = input_data.get("title", "Unknown")

        if not paper_text:
            raise ValueError("paper_text is required")

        # Use the agent to do initial analysis
        agent_input = f"""Analyze this paper titled "{title}".

Paper text:
{paper_text[:10000]}

Identify the main sections and structure."""

        agent_result = self.invoke_agent(agent_input)

        # Now use Instructor for structured output
        prompt = f"""Analyze this scientific paper and extract its logical structure.

Title: {title}

Paper text:
{paper_text}

Based on the paper, identify:
1. The main claim or thesis
2. Each logical step in the argument (typically 5-15 steps)
3. Dependencies between steps
4. Which section each step appears in

Agent's initial analysis:
{agent_result}
"""

        structure = self.get_structured_output(
            prompt=prompt,
            response_model=PaperStructure
        )

        return structure
