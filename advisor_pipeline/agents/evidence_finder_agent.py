import re
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

        if not paper_structure:
            raise ValueError("paper_structure is required")
        if not paper_text:
            raise ValueError("paper_text is required")

        # Run regex searches once on the full paper
        figures_found = self._search_for_figures(paper_text)
        equations_found = self._search_for_equations(paper_text)
        citations_found = self._search_for_citations(paper_text)

        all_step_evidence = []

        for step in paper_structure.logical_steps:
            print(f"Finding evidence for step {step.step_number}: {step.description[:100]}...")

            prompt = f"""You are a scientific evidence analyst. Extract all evidence supporting this step:

Step {step.step_number}: {step.description}
Section: {step.section}

References found in the paper:
- {figures_found}
- {equations_found}
- {citations_found}

Paper text:
{paper_text}

List ALL evidence for this step, including:
- Figures (with figure numbers)
- Math/equations (with equation numbers)
- Citations (with citation info)
- Important textual arguments

Be thorough - one step may have multiple pieces of evidence."""

            step_evidence = self.get_structured_output(
                prompt=prompt,
                response_model=StepEvidence
            )

            all_step_evidence = all_step_evidence + [step_evidence]

        return all_step_evidence

