from typing import Any, Dict, List
from pathlib import Path
from langchain_core.tools import Tool
import base64
from anthropic import Anthropic

from advisor_pipeline.agents.base_agent import BaseAgent
from advisor_pipeline.config.settings import settings
from advisor_pipeline.models.schemas import Evidence, FigureEvaluation, FigureInfo, ClaimValidity


class FigureEvaluatorAgent(BaseAgent):
    """
    Agent responsible for evaluating figure-based evidence.

    Input: List of figure evidence and figure file paths
    Output: List of FigureEvaluation
    """

    def __init__(self):
        super().__init__(
            name="FigureEvaluator",
            description="Evaluates whether figures actually support the claims made about them"
        )
        self.tools = self.get_tools()

        system_prompt = """You are a scientific figure analyst. For each figure:
1. Examine what data is actually shown
2. Extract numerical values and their units
3. Compare what the figure shows to what the paper claims it shows
4. Identify confirmations (where figure supports claim) and contradictions (where it doesn't)

Be precise with numbers and units. Be skeptical - verify claims against actual data."""

        self.initialize_agent()
    
    def get_tools(self):
        """Define tools for figure analysis."""
        
        def load_figure(figure_path: str) -> str:
            """Load a figure file and return its base64 encoding."""
            try:
                path = Path(figure_path)
                if not path.exists():
                    return f"Error: Figure not found at {figure_path}"
                
                with open(path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    return f"Successfully loaded figure: {path.name} ({len(image_data)} bytes)"
            except Exception as e:
                return f"Error loading figure: {str(e)}"
        
        def extract_figure_metadata(figure_path: str) -> str:
            """Extract metadata from figure file."""
            try:
                from PIL import Image
                img = Image.open(figure_path)
                return f"Figure size: {img.size}, Format: {img.format}, Mode: {img.mode}"
            except Exception as e:
                return f"Could not extract metadata: {str(e)}"
        
        return [
            Tool(
                name="load_figure",
                func=load_figure,
                description="Load a figure file for analysis"
            ),
            Tool(
                name="extract_figure_metadata",
                func=extract_figure_metadata,
                description="Get metadata about a figure file"
            )
        ]
    
    def run(self, input_data: Dict[str, Any]) -> List[FigureEvaluation]:
        """
        Evaluate all figure-based evidence.
        
        Args:
            input_data: Must contain:
                - 'evidence_list': List[Evidence] filtered to figure evidence
                - 'figures': Dict mapping figure names to file paths
                - 'claims': Dict mapping step numbers to their claims
                
        Returns:
            List of FigureEvaluation objects
        """
        evidence_list: List[Evidence] = input_data.get("evidence_list", [])
        figures: Dict[str, str] = input_data.get("figures", {})
        claims: Dict[int, str] = input_data.get("claims", {})
        
        # Filter to only figure evidence
        figure_evidence = [e for e in evidence_list if e.evidence_type == "figure"]
        
        if not figure_evidence:
            print("No figure evidence to evaluate")
            return []
        
        evaluations = []
        
        for evidence in figure_evidence:
            print(f"Evaluating figure evidence: {evidence.location}")
            
            # Extract figure name from location (e.g., "Figure 3" -> "figure_3")
            figure_name = evidence.location.lower().replace(" ", "_").replace(".", "")
            figure_path = figures.get(figure_name)
            
            if not figure_path:
                print(f"Warning: Figure {figure_name} not found in provided figures")
                continue

            # Get the claim this figure is supposed to support
            claim = claims.get(evidence.supports_step, "Unknown claim")

            # If figure file exists on disk, use vision-based evaluation
            if figure_path and Path(figure_path).exists():
                print(f"Using vision analysis for {evidence.location}")
                evaluation = self.evaluate_with_vision(figure_path, claim, evidence.supports_step)
            else:
                # Fallback: text-only evaluation when no figure file is available
                # Use agent to analyze the figure
                agent_input = f"""Analyze this figure:

Figure: {evidence.location}
Path: {figure_path}
Purpose: {evidence.description}
Supporting claim: {claim}

Load the figure and extract metadata."""

                agent_result = self.invoke_agent(agent_input)

                prompt = f"""Evaluate this figure-based evidence:

Figure: {evidence.location}
What it claims to show: {evidence.description}
Supporting step {evidence.supports_step}: {claim}

Agent analysis:
{agent_result}

NOTE: In this version, we don't have the actual figure image yet.
Base your evaluation on:
1. What the paper CLAIMS the figure shows (from description)
2. Whether those claims are specific and verifiable
3. What you would expect to see if you had the figure

Extract any numerical values mentioned, note confirmations and contradictions.
"""

                evaluation = self.get_structured_output(
                    prompt=prompt,
                    response_model=FigureEvaluation,
                    context={
                        "figure_name": evidence.location,
                        "supports_step": evidence.supports_step
                    }
                )

            evaluations.append(evaluation)
        
        return evaluations
    
    def evaluate_with_vision(self, figure_path: str, claim: str, step_number: int) -> FigureEvaluation:
        """Evaluate figure using Claude's vision capabilities."""
        path = Path(figure_path)
        if not path.exists():
            return FigureEvaluation(
                figure_name=path.name,
                supports_step=step_number,
                extracted_data=[],
                validity=ClaimValidity(confirmations=[], contradictions=["Figure file not found"]),
                notes=f"Could not find figure at {figure_path}",
            )

        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Determine media type
        suffix = path.suffix.lower()
        media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
        media_type = media_types.get(suffix, "image/png")

        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.model_name,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": image_data},
                        },
                        {
                            "type": "text",
                            "text": f"""Analyze this scientific figure. The paper claims it supports: "{claim}"

Please:
1. Describe what the figure actually shows (data, axes, trends)
2. Extract any specific numerical values with units
3. List confirmations: ways the figure supports the claim
4. List contradictions: ways the figure does NOT support the claim or shows something different
5. Note anything unusual or concerning about the figure

Be precise with numbers and units. Be skeptical.""",
                        },
                    ],
                }
            ],
        )

        # Parse the vision response into structured output
        vision_text = response.content[0].text

        evaluation = self.get_structured_output(
            prompt=f"""Based on this vision analysis of a figure, create a structured evaluation:

Vision analysis:
{vision_text}

The figure was claimed to support: "{claim}"
Figure name: {path.name}
Step number: {step_number}

Extract numerical data, confirmations, and contradictions from the analysis.""",
            response_model=FigureEvaluation,
            context={"figure_name": path.name, "supports_step": step_number},
        )

        return evaluation
