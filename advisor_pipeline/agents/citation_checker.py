"""Citation checker — verifies citations actually support claims.

Uses a LangGraph ReAct agent with Semantic Scholar tools, then structures
the result as CitationCheck via get_structured_output().
"""

import re
from typing import Dict, List

import httpx
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent

from advisor_pipeline.llm import get_llm, get_structured_output
from advisor_pipeline.mcp_servers.advisor_server.prompts import CITATION_REPORTER, CITATION_VERIFIER
from advisor_pipeline.models.schemas import CitationCheck, Evidence


class CitationChecker:
    """Verifies citation-based evidence without BaseAgent inheritance.

    Uses a create_react_agent loop with 4 Semantic Scholar tools.
    """

    def __init__(self):
        self._tools = self._build_tools()
        self._agent = create_react_agent(get_llm().bind_tools(self._tools), self._tools)

    def _build_tools(self) -> list[Tool]:
        def extract_doi(citation: str) -> str:
            """Extract DOI from citation text."""
            doi_pattern = r"10\.\d{4,}/[^\s]+"
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
                    authors_list = paper.get("authors", [])
                    author_names = ", ".join(a.get("name", "Unknown") for a in authors_list[:3])
                    if len(authors_list) > 3:
                        author_names += " et al."
                    external_ids = paper.get("externalIds", {}) or {}
                    doi = external_ids.get("DOI", "N/A")
                    lines.append(
                        f'{i}. "{title}"\n'
                        f"   Authors: {author_names}\n"
                        f"   Year: {year}\n"
                        f"   DOI: {doi}\n"
                        f"   ID: {paper.get('paperId', 'N/A')}\n"
                    )
                return "\n".join(lines)
            except Exception as e:
                return f"Error searching: {e}"

        def check_accessibility(doi_or_url: str) -> str:
            """Check if a paper is publicly accessible via Semantic Scholar."""
            try:
                identifier = doi_or_url.strip()
                if identifier.startswith("10."):
                    api_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{identifier}"
                else:
                    api_url = f"https://api.semanticscholar.org/graph/v1/paper/{identifier}"

                response = httpx.get(
                    api_url, params={"fields": "isOpenAccess,openAccessPdf,url"}, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                is_oa = data.get("isOpenAccess", False)
                pdf = data.get("openAccessPdf")
                lines = [
                    f"Accessibility for '{doi_or_url}':",
                    f"  URL: {data.get('url', 'N/A')}",
                    f"  Open Access: {'Yes' if is_oa else 'No'}",
                    f"  PDF: {pdf['url'] if pdf and pdf.get('url') else 'Not available'}",
                ]
                return "\n".join(lines)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return f"Paper not found: '{doi_or_url}'"
                return f"HTTP error: {e.response.status_code}"
            except Exception as e:
                return f"Error: {e}"

        def get_paper_abstract(doi_or_url: str) -> str:
            """Retrieve abstract of a cited paper via Semantic Scholar."""
            try:
                identifier = doi_or_url.strip()
                if identifier.startswith("10."):
                    api_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{identifier}"
                else:
                    api_url = f"https://api.semanticscholar.org/graph/v1/paper/{identifier}"

                response = httpx.get(
                    api_url, params={"fields": "abstract,title,authors,year"}, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                authors_list = data.get("authors", [])
                author_names = ", ".join(a.get("name", "Unknown") for a in authors_list[:5])
                if len(authors_list) > 5:
                    author_names += " et al."
                abstract = data.get("abstract", "No abstract available.")
                return (
                    f"Title: {data.get('title', 'Unknown')}\n"
                    f"Authors: {author_names}\n"
                    f"Year: {data.get('year', 'Unknown')}\n\n"
                    f"Abstract: {abstract}"
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return f"Paper not found: '{doi_or_url}'"
                return f"HTTP error: {e.response.status_code}"
            except Exception as e:
                return f"Error: {e}"

        return [
            Tool(
                name="extract_doi", func=extract_doi, description="Extract DOI from citation text"
            ),
            Tool(
                name="search_paper_database",
                func=search_paper_database,
                description="Search for a paper in academic databases",
            ),
            Tool(
                name="check_accessibility",
                func=check_accessibility,
                description="Check if a paper is publicly accessible",
            ),
            Tool(
                name="get_paper_abstract",
                func=get_paper_abstract,
                description="Retrieve the abstract of a cited paper",
            ),
        ]

    def run(
        self,
        evidence_list: List[Evidence],
        paper_text: str,
        claims: Dict[int, str],
        bibliography: Dict[str, str] | None = None,
    ) -> List[CitationCheck]:
        """Verify all citation-based evidence.

        Args:
            evidence_list: Evidence items (already filtered to citation type).
            paper_text: Full paper text.
            claims: Dict mapping step numbers to claim descriptions.
            bibliography: Optional dict of citation references.

        Returns:
            List of CitationCheck objects.
        """
        bibliography = bibliography or {}
        citation_evidence = [e for e in evidence_list if e.evidence_type == "citation"]
        if not citation_evidence:
            print("No citation evidence to check")
            return []

        checks = []

        for evidence in citation_evidence:
            print(f"Checking citation: {evidence.location}")
            claim = claims.get(evidence.supports_step, "Unknown claim")
            full_citation = self._find_full_citation(evidence.location, paper_text, bibliography)

            # Run the agent
            agent_input = CITATION_VERIFIER.format(
                citation_location=evidence.location,
                full_citation=full_citation,
                claim=claim,
                citation_description=evidence.description,
            )
            result = self._agent.invoke(
                {"messages": [HumanMessage(content=agent_input)]},
                {"recursion_limit": 10},
            )
            agent_result = result["messages"][-1].content if result.get("messages") else ""

            # Structure the result
            prompt = CITATION_REPORTER.format(
                citation_location=evidence.location,
                full_citation=full_citation,
                supports_step=evidence.supports_step,
                claim=claim,
                agent_result=agent_result,
            )
            check = get_structured_output(CitationCheck, prompt)
            checks.append(check)

        return checks

    @staticmethod
    def _find_full_citation(
        citation_ref: str, paper_text: str, bibliography: Dict[str, str]
    ) -> str:
        if bibliography and citation_ref in bibliography:
            return bibliography[citation_ref]

        ref_num = re.search(r"\d+", citation_ref)
        if ref_num:
            bib_pattern = f"\\[{ref_num.group()}\\].*?(?=\\[\\d+\\]|$)"
            match = re.search(bib_pattern, paper_text, re.DOTALL)
            if match:
                return match.group(0)[:500]

        return f"Citation {citation_ref} (full details not found)"
