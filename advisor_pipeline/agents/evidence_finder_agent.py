from typing import Any, Dict, List
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate

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
        self.tools = self.get_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a scientific evidence analyst. For each logical step in a paper:
1. Find all evidence cited to support that step
2. Classify evidence as: figure, math/equation, citation, or textual argument
3. Note the exact location (section, page, figure number, equation number)
4. Describe what the evidence shows

Be thorough - one step may have multiple pieces of evidence."""),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        self.initialize_agent(prompt)
    
    def get_tools(self):
        """Define tools for evidence searching."""
        
        def search_for_figures(text: str, step_desc: str) -> str:
            """Search for figure references related to a step."""
            import re
            # Look for "Figure X" or "Fig. X" patterns
            figures = re.findall(r'[Ff]ig(?:ure)?\.?\s*(\d+[a-z]?)', text)
            return f"Found figure references: {', '.join(set(figures))}"
        
        def search_for_equations(text: str, step_desc: str) -> str:
            """Search for equation references related to a step."""
            import re
            equations = re.findall(r'[Ee]q(?:uation)?\.?\s*\(?(\d+)\)?', text)
            return f"Found equation references: {', '.join(set(equations))}"
        
        def search_for_citations(text: str, step_desc: str) -> str:
            """Search for citation patterns."""
            import re
            # Look for [1], (Author, Year) patterns
            citations = re.findall(r'\[(\d+(?:,\s*\d+)*)\]|\(([A-Z][a-z]+(?:\s+et\s+al\.?)?,\s*\d{4})\)', text)
            flat_citations = [c for group in citations for c in group if c]
            return f"Found {len(flat_citations)} citations"
        
        return [
            Tool(
                name="search_for_figures",
                func=search_for_figures,
                description="Find figure references in the paper text"
            ),
            Tool(
                name="search_for_equations",
                func=search_for_equations,
                description="Find equation references in the paper text"
            ),
            Tool(
                name="search_for_citations",
                func=search_for_citations,
                description="Find citation references in the paper text"
            )
        ]
    
    def run(self, input_data: Dict[str, Any]) -> List[StepEvidence]:
        """
        Find evidence for each logical step.
        
        Args:
            input_data: Must contain 'paper_structure' and 'paper_text'
            
        Returns:
            List of StepEvidence objects, one per logical step
        """
        paper_structure: PaperStructure = input_data.get("paper_structure")
        paper_text: str = input_data.get("paper_text", "")
        
        if not paper_structure:
            raise ValueError("paper_structure is required")
        if not paper_text:
            raise ValueError("paper_text is required")
        
        all_step_evidence = []
        
        # Process each logical step
        for step in paper_structure.logical_steps:
            print(f"Finding evidence for step {step.step_number}: {step.description[:100]}...")
            
            # Use agent to search for evidence
            agent_input = f"""Find all evidence supporting this logical step:

Step {step.step_number}: {step.description}
Section: {step.section}

Search the paper for:
- Figures that support this step
- Equations or mathematical derivations
- Citations to other papers
- Key textual arguments

Paper excerpt from {step.section}:
{self._extract_section(paper_text, step.section)}
"""
            
            agent_result = self.agent_executor.invoke({"input": agent_input})
            
            # Use Instructor to structure the evidence
            prompt = f"""Extract all evidence supporting this step:

Step {step.step_number}: {step.description}

Agent found:
{agent_result.get('output', '')}

Full context:
{paper_text}

List ALL evidence for this step, including:
- Figures (with figure numbers)
- Math/equations (with equation numbers)
- Citations (with citation info)
- Important textual arguments
"""
            
            # Get structured evidence list
            class EvidenceList(BaseModel):
                evidence: List[Evidence]
            
            from pydantic import BaseModel
            evidence_result = self.get_structured_output(
                prompt=prompt,
                response_model=EvidenceList
            )
            
            step_evidence = StepEvidence(
                step_number=step.step_number,
                evidence_list=evidence_result.evidence
            )
            all_step_evidence.append(step_evidence)
        
        return all_step_evidence
    
    def _extract_section(self, text: str, section_name: str, context_chars: int = 2000) -> str:
        """Extract text from a specific section."""
        # Simple heuristic: find section header and grab surrounding text
        import re
        pattern = re.escape(section_name)
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            start = max(0, match.start() - context_chars // 2)
            end = min(len(text), match.end() + context_chars)
            return text[start:end]
        
        return text[:context_chars]  # Fallback to beginning
