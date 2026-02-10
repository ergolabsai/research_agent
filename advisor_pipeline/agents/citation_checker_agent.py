from typing import Any, Dict, List
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate
import re

from agents.base_agent import BaseAgent
from models.schemas import Evidence, CitationCheck


class CitationCheckerAgent(BaseAgent):
    """
    Agent responsible for verifying citations actually support the claims.
    
    Input: List of citation evidence
    Output: List of CitationCheck
    """
    
    def __init__(self):
        super().__init__(
            name="CitationChecker",
            description="Verifies that citations actually support the claims attributed to them"
        )
        self.tools = self.get_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a citation verification specialist. For each citation:
1. Try to locate the cited paper (DOI, arXiv, etc.)
2. If accessible, read the abstract and relevant sections
3. Verify whether it actually supports the claim being made
4. Note any discrepancies

Be thorough - misrepresenting citations is a serious issue in scientific publishing."""),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        self.initialize_agent(prompt)
    
    def get_tools(self):
        """Define tools for citation checking."""
        
        def extract_doi(citation: str) -> str:
            """Extract DOI from a citation string."""
            # Look for DOI patterns
            doi_pattern = r'10\.\d{4,}/[^\s]+'
            match = re.search(doi_pattern, citation)
            if match:
                return f"Found DOI: {match.group(0)}"
            return "No DOI found in citation"
        
        def search_paper_database(query: str) -> str:
            """
            Search for a paper (placeholder for actual API integration).
            
            In production, this would call APIs like:
            - Semantic Scholar API
            - CrossRef API
            - arXiv API
            - PubMed API
            """
            # TODO: Integrate with actual paper databases
            return f"Placeholder: Would search for '{query}' in paper databases"
        
        def check_accessibility(doi_or_url: str) -> str:
            """Check if a paper is publicly accessible."""
            # TODO: Actually check if paper is accessible
            # For now, just return a placeholder
            return f"Placeholder: Would check accessibility of {doi_or_url}"
        
        def get_paper_abstract(doi_or_url: str) -> str:
            """Retrieve abstract of a cited paper."""
            # TODO: Integrate with paper APIs to get abstracts
            return f"Placeholder: Would retrieve abstract for {doi_or_url}"
        
        return [
            Tool(
                name="extract_doi",
                func=extract_doi,
                description="Extract DOI from citation text"
            ),
            Tool(
                name="search_paper_database",
                func=search_paper_database,
                description="Search for a paper in academic databases"
            ),
            Tool(
                name="check_accessibility",
                func=check_accessibility,
                description="Check if a paper is publicly accessible"
            ),
            Tool(
                name="get_paper_abstract",
                func=get_paper_abstract,
                description="Retrieve the abstract of a cited paper"
            )
        ]
    
    def run(self, input_data: Dict[str, Any]) -> List[CitationCheck]:
        """
        Verify all citation-based evidence.
        
        Args:
            input_data: Must contain:
                - 'evidence_list': List[Evidence] filtered to citation evidence
                - 'paper_text': Full paper text to find citation details
                - 'claims': Dict mapping step numbers to claims
                - 'bibliography': Optional dict of citations
                
        Returns:
            List of CitationCheck objects
        """
        evidence_list: List[Evidence] = input_data.get("evidence_list", [])
        paper_text: str = input_data.get("paper_text", "")
        claims: Dict[int, str] = input_data.get("claims", {})
        bibliography: Dict[str, str] = input_data.get("bibliography", {})
        
        # Filter to only citation evidence
        citation_evidence = [e for e in evidence_list if e.evidence_type == "citation"]
        
        if not citation_evidence:
            print("No citation evidence to check")
            return []
        
        checks = []
        
        for evidence in citation_evidence:
            print(f"Checking citation: {evidence.location}")
            
            # Get the claim this citation supports
            claim = claims.get(evidence.supports_step, "Unknown claim")
            
            # Extract full citation from bibliography or paper text
            full_citation = self._find_full_citation(
                evidence.location,
                paper_text,
                bibliography
            )
            
            # Use agent to verify the citation
            agent_input = f"""Verify this citation:

Citation reference: {evidence.location}
Full citation: {full_citation}
Claim it supports: {claim}
Context: {evidence.description}

Tasks:
1. Extract DOI if available
2. Search for the paper in databases
3. Check if it's accessible
4. If accessible, get the abstract
"""
            
            agent_result = self.agent_executor.invoke({"input": agent_input})
            
            # Use Instructor to structure the verification result
            prompt = f"""Create a citation verification report:

Citation: {evidence.location}
Full citation details: {full_citation}
Supports step {evidence.supports_step}: {claim}

Agent's investigation:
{agent_result.get('output', '')}

Determine:
1. Whether the citation is accessible
2. If accessible, whether it supports the claim
3. Any notes about the verification
"""
            
            check = self.get_structured_output(
                prompt=prompt,
                response_model=CitationCheck,
                context={
                    "citation": full_citation or evidence.location,
                    "supports_step": evidence.supports_step
                }
            )
            
            checks.append(check)
        
        return checks
    
    def _find_full_citation(self, citation_ref: str, paper_text: str,
                           bibliography: Dict[str, str]) -> str:
        """Find the full citation from reference number."""
        
        # Try bibliography first
        if bibliography and citation_ref in bibliography:
            return bibliography[citation_ref]
        
        # Try to find in paper text
        # Look for patterns like "[1]" or "(Smith et al., 2020)"
        ref_num = re.search(r'\d+', citation_ref)
        if ref_num:
            # Search for this reference number in the bibliography section
            bib_pattern = f"\\[{ref_num.group()}\\].*?(?=\\[\\d+\\]|$)"
            match = re.search(bib_pattern, paper_text, re.DOTALL)
            if match:
                return match.group(0)[:500]  # Limit length
        
        return f"Citation {citation_ref} (full details not found)"
