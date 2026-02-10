from typing import Any, Dict, List
from pathlib import Path
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate
import base64

from agents.base_agent import BaseAgent
from models.schemas import Evidence, FigureEvaluation, FigureInfo, ClaimValidity


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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a scientific figure analyst. For each figure:
1. Examine what data is actually shown
2. Extract numerical values and their units
3. Compare what the figure shows to what the paper claims it shows
4. Identify confirmations (where figure supports claim) and contradictions (where it doesn't)

Be precise with numbers and units. Be skeptical - verify claims against actual data."""),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        self.initialize_agent(prompt)
    
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
            
            # Use agent to analyze the figure
            agent_input = f"""Analyze this figure:

Figure: {evidence.location}
Path: {figure_path}
Purpose: {evidence.description}
Supporting claim: {claim}

Load the figure and extract metadata."""
            
            agent_result = self.agent_executor.invoke({"input": agent_input})
            
            # For now, we'll use Instructor without vision (placeholder for future OCR)
            # In production, you'd send the actual image to Claude with vision
            prompt = f"""Evaluate this figure-based evidence:

Figure: {evidence.location}
What it claims to show: {evidence.description}
Supporting step {evidence.supports_step}: {claim}

Agent analysis:
{agent_result.get('output', '')}

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
    
    def evaluate_with_vision(self, figure_path: str, claim: str) -> FigureEvaluation:
        """
        Future method: Evaluate figure using Claude's vision capabilities.
        
        This is a placeholder for when you integrate actual image analysis.
        """
        # TODO: Implement vision-based figure analysis
        # Will use Anthropic's vision API to analyze actual figure images
        pass
