from typing import Any, Dict, List

from advisor_pipeline.agents.base_agent import BaseAgent
from advisor_pipeline.models.schemas import PaperStructure, StepEvidence


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
        figure_names: list = input_data.get("figure_names", [])

        all_step_evidence = []

        figure_names_str = ", ".join(figure_names) if figure_names else "None provided"

        paper_structure.logical_steps = sorted(paper_structure.logical_steps, key=lambda s: s.step_number)

        for step in paper_structure.logical_steps:
            print(f"Finding evidence for step {step.step_number}: {step.description[:100]}...")

            step_evidence = self.get_structured_output(
                prompt=f"""Extract all evidence supporting this logical step from the research paper.

Step {step.step_number}: {step.description}
Section: {step.section}

Available figure files: {figure_names_str}

Paper text:
{paper_text}

List ALL evidence for this step, including:
- Figures (with figure numbers). When referencing a figure, use the exact filename from the available figure files list above.
- Math/equations (with equation numbers)
- Citations (with citation info)
- Important textual arguments

Be thorough - one step may have multiple pieces of evidence.""",
                response_model=StepEvidence
            )

            all_step_evidence = all_step_evidence + [step_evidence]

            if step.step_number > 2:
                break

        return all_step_evidence

