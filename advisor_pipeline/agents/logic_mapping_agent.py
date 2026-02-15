from typing import Any, Dict

from advisor_pipeline.agents.base_agent import BaseAgent
from advisor_pipeline.models.schemas import PaperStructure, LogicalStep


class LogicMappingAgent(BaseAgent):
    """
    Agent responsible for identifying key logical steps.

    Input: Full paper text
    Output: PaperStructure with ordered logical steps
    """

    def __init__(self):
        super().__init__(
            name="PaperReader",
            description="Reads scientific papers and extracts the logical argument structure"
        )

        self.initialize_agent()
    
    def get_tools(self):
        return []
    
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
        instructor_prompt = f"""A previous agent was asked to find the structure of a research paper.
You're job is to now properly format its response.  

Your response should be in the form:

    title: str = Field(description="Paper title")
    main_claim: str = Field(description="The paper's primary claim or thesis")
    logical_steps: List[LogicalStep] = Field(description="Ordered list of logical steps")

Here is the paper:
{paper_text}

Here is the agent's initial analysis:
{agent_result}
"""

        structure = self.get_structured_output(
            prompt=instructor_prompt,
            response_model=PaperStructure
        )

        return structure
