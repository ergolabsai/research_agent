from typing import Any, Dict, List

from advisor_pipeline.agents.base_agent import BaseAgent
from advisor_pipeline.models.schemas import PaperStructure, Evidence, StepEvidence


class EvidenceFinderAgent(BaseAgent):
    """
    Agent responsible for finding evidence supporting each logical step.

    Input: PaperStructure and full paper text
    Output: List of StepEvidence (one per logical step)
    """

    def __init__(self):
        super().__init__(
            name="EvidenceFinder",
            description="Finds and catalogs evidence supporting each logical step"
        )

        self.initialize_agent()

    def get_tools(self):
        return []

    def run(self, input_data: Dict[str, Any]) -> List[StepEvidence]:
        """
        Find evidence for each logical step.

        Args:
            input_data: Must contain 'paper_structure' and 'paper_text'

        Returns:
            List of StepEvidence objects, one per logical step
        """
        paper_structure: PaperStructure = input_data.get("paper_structure")
        paper_text: str = input_data.get("paper_text")

        all_step_evidence = []

        paper_structure.logical_steps = sorted(paper_structure.logical_steps, key=lambda s: s.step_number)

        for step in paper_structure.logical_steps:
            print(f"Finding evidence for step {step.step_number}: {step.description[:100]}...")

            agent_input = f"""You are a scientific evidence analyst. Extract all evidence supporting this step:

Step {step.step_number}: {step.description}
Section: {step.section}

Paper text:
{paper_text}

List ALL evidence for this step, including:
- Figures (with figure numbers)
- Math/equations (with equation numbers)
- Citations (with citation info)
- Important textual arguments

Be thorough - one step may have multiple pieces of evidence."""

            agent_result = self.invoke_agent(agent_input)

            # Now use Instructor for structured output
            instructor_prompt = f"""A previous agent was asked to find evidence that supports a claim in a research paper.
            You're job is to now properly format its response.  

            Your response should be in the form:

                evidence_type: str = Field(description="Type: 'figure', 'math', 'citation', or 'text'")
                description: str = Field(description="What this evidence shows")
                location: str = Field(description="Where in the paper (section, page, figure number, etc.)")
                supports_step: int = Field(description="Which logical step this supports")

            Here is the paper:
            {paper_text}

            Here is the agent's initial analysis:
            {agent_result}
            """

            step_evidence = self.get_structured_output(
                prompt=instructor_prompt,
                response_model=StepEvidence
            )

            all_step_evidence = all_step_evidence + [(step, step_evidence)]

        return all_step_evidence

