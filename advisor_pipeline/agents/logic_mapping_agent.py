from typing import Any, Dict

from advisor_pipeline.agents.base_agent import BaseAgent
from advisor_pipeline.models.schemas import PaperStructure


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

        if not paper_text:
            raise ValueError("paper_text is required")

        return self.get_structured_output(
            prompt=f"""Analyze the following research paper. Identify:
1. The paper's title
2. The paper's primary claim or thesis
3. The ordered logical steps of the argument, including what each step claims,
   which previous steps it depends on, and which section it appears in

Paper text:
{paper_text}""",
            response_model=PaperStructure
        )
