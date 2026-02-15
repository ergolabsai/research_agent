from typing import Any, Dict, List
from langchain_core.tools import Tool
import re
import httpx

from advisor_pipeline.agents.base_agent import BaseAgent
from advisor_pipeline.models.schemas import Evidence, CitationCheck


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

        system_prompt = """You are a citation verification specialist. For each citation:
1. Try to locate the cited paper (DOI, arXiv, etc.)
2. If accessible, read the abstract and relevant sections
3. Verify whether it actually supports the claim being made
4. Note any discrepancies

Be thorough - misrepresenting citations is a serious issue in scientific publishing."""

        self.initialize_agent()
    
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
            """Search for a paper using the Semantic Scholar API."""
            try:
                response = httpx.get(
                    "https://api.semanticscholar.org/graph/v1/paper/search",
                    params={
                        "query": query,
                        "limit": 5,
                        "fields": "title,authors,year,abstract,externalIds",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                results = data.get("data", [])
                if not results:
                    return f"No results found for query: '{query}'"

                lines = [f"Found {len(results)} result(s) for '{query}':\n"]
                for i, paper in enumerate(results, 1):
                    title = paper.get("title", "Unknown title")
                    year = paper.get("year", "Unknown year")
                    paper_id = paper.get("paperId", "N/A")
                    authors_list = paper.get("authors", [])
                    author_names = ", ".join(
                        a.get("name", "Unknown") for a in authors_list[:3]
                    )
                    if len(authors_list) > 3:
                        author_names += " et al."
                    external_ids = paper.get("externalIds", {}) or {}
                    doi = external_ids.get("DOI", "N/A")

                    lines.append(
                        f"{i}. \"{title}\"\n"
                        f"   Authors: {author_names}\n"
                        f"   Year: {year}\n"
                        f"   DOI: {doi}\n"
                        f"   Semantic Scholar ID: {paper_id}\n"
                    )
                return "\n".join(lines)
            except httpx.HTTPStatusError as e:
                return f"HTTP error searching for '{query}': {e.response.status_code} {e.response.reason_phrase}"
            except httpx.RequestError as e:
                return f"Request error searching for '{query}': {str(e)}"
            except Exception as e:
                return f"Unexpected error searching for '{query}': {str(e)}"
        
        def check_accessibility(doi_or_url: str) -> str:
            """Check if a paper is publicly accessible via the Semantic Scholar API."""
            try:
                identifier = doi_or_url.strip()
                if identifier.startswith("10."):
                    api_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{identifier}"
                else:
                    api_url = f"https://api.semanticscholar.org/graph/v1/paper/{identifier}"

                response = httpx.get(
                    api_url,
                    params={"fields": "isOpenAccess,openAccessPdf,url"},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                is_open_access = data.get("isOpenAccess", False)
                open_access_pdf = data.get("openAccessPdf")
                paper_url = data.get("url", "N/A")

                lines = [f"Accessibility check for '{doi_or_url}':"]
                lines.append(f"  Semantic Scholar URL: {paper_url}")
                lines.append(f"  Open Access: {'Yes' if is_open_access else 'No'}")
                if open_access_pdf and open_access_pdf.get("url"):
                    lines.append(f"  Open Access PDF: {open_access_pdf['url']}")
                else:
                    lines.append("  Open Access PDF: Not available")

                return "\n".join(lines)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return f"Paper not found in Semantic Scholar for identifier: '{doi_or_url}'"
                return f"HTTP error checking accessibility for '{doi_or_url}': {e.response.status_code} {e.response.reason_phrase}"
            except httpx.RequestError as e:
                return f"Request error checking accessibility for '{doi_or_url}': {str(e)}"
            except Exception as e:
                return f"Unexpected error checking accessibility for '{doi_or_url}': {str(e)}"
        
        def get_paper_abstract(doi_or_url: str) -> str:
            """Retrieve abstract of a cited paper via the Semantic Scholar API."""
            try:
                identifier = doi_or_url.strip()
                if identifier.startswith("10."):
                    api_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{identifier}"
                else:
                    api_url = f"https://api.semanticscholar.org/graph/v1/paper/{identifier}"

                response = httpx.get(
                    api_url,
                    params={"fields": "abstract,title,authors,year"},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                title = data.get("title", "Unknown title")
                year = data.get("year", "Unknown year")
                abstract = data.get("abstract")
                authors_list = data.get("authors", [])
                author_names = ", ".join(
                    a.get("name", "Unknown") for a in authors_list[:5]
                )
                if len(authors_list) > 5:
                    author_names += " et al."

                lines = [
                    f"Title: {title}",
                    f"Authors: {author_names}",
                    f"Year: {year}",
                    "",
                    f"Abstract: {abstract if abstract else 'No abstract available.'}",
                ]
                return "\n".join(lines)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return f"Paper not found in Semantic Scholar for identifier: '{doi_or_url}'"
                return f"HTTP error retrieving abstract for '{doi_or_url}': {e.response.status_code} {e.response.reason_phrase}"
            except httpx.RequestError as e:
                return f"Request error retrieving abstract for '{doi_or_url}': {str(e)}"
            except Exception as e:
                return f"Unexpected error retrieving abstract for '{doi_or_url}': {str(e)}"
        
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
            
            agent_result = self.invoke_agent(agent_input)

            # Use Instructor to structure the verification result
            prompt = f"""Create a citation verification report:

Citation: {evidence.location}
Full citation details: {full_citation}
Supports step {evidence.supports_step}: {claim}

Agent's investigation:
{agent_result}

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
