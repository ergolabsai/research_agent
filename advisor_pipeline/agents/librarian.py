"""Librarian agent — finds related papers and scores relevancy + convergence.

Replaces the old CitationChecker.  Runs in two passes:
  1. gather_papers  (early pass)  — find cited + related papers via LanceDB & Semantic Scholar
  2. score_papers   (late pass)   — LLM scores each paper for relevancy & convergence

Uses:
  - LanceDB full-text search (for cited papers by title)
  - LanceDB vector search   (for additional related papers via LLM-crafted queries)
  - Semantic Scholar API     (fallback when LanceDB FTS misses a cited paper)
"""

import re
from typing import Dict, List

import httpx
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from advisor_pipeline.llm import get_structured_output, invoke_text
from advisor_pipeline.mcp_servers.advisor_server.prompts import (
    LIBRARIAN_CONTEXT,
    LIBRARIAN_QUERY_CRAFTER,
    LIBRARIAN_SCORER,
)
from advisor_pipeline.models.schemas import (
    LibrarianResult,
    PaperStructure,
    RelatedPaper,
    RelatedPaperScored,
    SearchQueries,
)
from advisor_pipeline.utils.lancedb_search import fts_search, vector_search


# ---------------------------------------------------------------------------
# Semantic Scholar helpers (kept from old CitationChecker as fallback)
# ---------------------------------------------------------------------------

def _search_semantic_scholar(query: str, limit: int = 3) -> List[dict]:
    """Search Semantic Scholar API. Returns list of paper dicts."""
    try:
        response = httpx.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": limit,
                "fields": "title,authors,year,abstract,externalIds",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception:
        return []


def _semantic_scholar_to_related(papers: list) -> List[RelatedPaper]:
    """Convert Semantic Scholar results to RelatedPaper objects (unscored)."""
    results = []
    for p in papers:
        authors_list = p.get("authors", [])
        author_str = ", ".join(a.get("name", "") for a in authors_list[:5])
        if len(authors_list) > 5:
            author_str += " et al."
        ext_ids = p.get("externalIds", {}) or {}
        pid = ext_ids.get("DOI") or ext_ids.get("ArXiv") or p.get("paperId", "")
        results.append(RelatedPaper(
            paper_id=pid,
            title=p.get("title", ""),
            authors=author_str,
            abstract=p.get("abstract", "") or "",
            source="semantic_scholar",
        ))
    return results


# ---------------------------------------------------------------------------
# LanceDB helpers
# ---------------------------------------------------------------------------

def _lancedb_rows_to_related(df: pd.DataFrame, source: str) -> List[RelatedPaper]:
    """Convert a LanceDB DataFrame to RelatedPaper objects (unscored)."""
    results = []
    if df is None or df.empty:
        return results
    for _, row in df.iterrows():
        results.append(RelatedPaper(
            paper_id=str(row.get("id", "")),
            title=str(row.get("title", "")),
            authors=str(row.get("authors", "")),
            abstract=str(row.get("abstract", "")),
            source=source,
        ))
    return results


# ---------------------------------------------------------------------------
# Librarian agent
# ---------------------------------------------------------------------------

class Librarian:
    """Finds related papers and scores them for relevancy and convergence.

    Two-pass design:
      - ``gather_papers`` runs early (before evidence-finding) to build context
      - ``score_papers`` runs late (after evaluations) to produce final scores
    """

    # ------------------------------------------------------------------
    # Pass 1 — Gather papers + enrich context
    # ------------------------------------------------------------------

    def gather_papers(
        self,
        paper_text: str,
        bibliography: Dict[str, str] | None = None,
        paper_structure: PaperStructure | None = None,
    ) -> LibrarianResult:
        """Find cited + related papers. Returns unscored LibrarianResult."""
        bibliography = bibliography or {}
        found: Dict[str, RelatedPaper] = {}  # keyed by paper_id to deduplicate

        # --- 1. Locate cited papers via LanceDB FTS, then Semantic Scholar fallback ---
        for ref_key, ref_text in bibliography.items():
            title = self._extract_title(ref_text)
            if not title:
                continue
            papers = self._find_cited_paper(title)
            for rp in papers:
                if rp.paper_id not in found:
                    found[rp.paper_id] = rp

        # --- 2. Craft vector search queries via LLM ---
        search_queries = self._craft_search_queries(paper_text, paper_structure)

        # --- 3. Run LanceDB vector search with crafted queries ---
        for query in search_queries:
            df = vector_search(query, limit=5)
            for rp in _lancedb_rows_to_related(df, "lancedb_vector"):
                if rp.paper_id not in found:
                    found[rp.paper_id] = rp

        related_papers = list(found.values())

        # --- 4. Generate context summary ---
        context_summary = self._generate_context_summary(
            paper_structure, related_papers
        )

        return LibrarianResult(
            related_papers=related_papers,
            context_summary=context_summary,
            search_queries=search_queries,
        )

    # ------------------------------------------------------------------
    # Pass 2 — Score each related paper
    # ------------------------------------------------------------------

    def score_papers(
        self,
        paper_text: str,
        paper_structure: PaperStructure,
        related_papers: List[RelatedPaper],
    ) -> List[RelatedPaper]:
        """Score every related paper for relevancy and convergence."""
        user_excerpt = paper_text[:3000]
        scored: List[RelatedPaper] = []

        for rp in related_papers:
            print(f"  Scoring: {rp.title[:80]}...")
            scores = self._score_single_paper(paper_structure, user_excerpt, rp)
            scored.append(RelatedPaper(
                paper_id=rp.paper_id,
                title=rp.title,
                authors=rp.authors,
                abstract=rp.abstract,
                source=rp.source,
                relevancy_score=scores.relevancy_score,
                relevancy_reasoning=scores.relevancy_reasoning,
                convergence_score=scores.convergence_score,
                convergence_reasoning=scores.convergence_reasoning,
            ))

        return scored

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_title(ref_text: str) -> str:
        """Best-effort extraction of a paper title from a bibliography entry."""
        # Try common patterns: "Title" or Title.  after authors
        # Pattern 1: text in quotes
        match = re.search(r'"([^"]{10,})"', ref_text)
        if match:
            return match.group(1).strip()
        # Pattern 2: text in curly braces (BibTeX)
        match = re.search(r"title\s*=\s*\{([^}]+)\}", ref_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Pattern 3: after first period (author list), take up to next period
        parts = ref_text.split(".")
        if len(parts) >= 2:
            candidate = parts[1].strip()
            if len(candidate) > 10:
                return candidate
        return ""

    def _find_cited_paper(self, title: str) -> List[RelatedPaper]:
        """Try LanceDB FTS first, fall back to Semantic Scholar."""
        # LanceDB FTS
        df = fts_search(title, limit=3)
        candidates = _lancedb_rows_to_related(df, "lancedb_fts")
        if candidates:
            return candidates[:1]  # best FTS hit

        # Semantic Scholar fallback
        ss_papers = _search_semantic_scholar(title, limit=2)
        return _semantic_scholar_to_related(ss_papers)[:1]

    def _craft_search_queries(
        self,
        paper_text: str,
        paper_structure: PaperStructure | None,
    ) -> List[str]:
        """Use the LLM to generate high-quality vector search queries."""
        title = paper_structure.title if paper_structure else "Unknown"
        main_claim = paper_structure.main_claim if paper_structure else ""
        excerpt = paper_text[:4000]

        prompt = LIBRARIAN_QUERY_CRAFTER.format(
            title=title,
            main_claim=main_claim,
            paper_text_excerpt=excerpt,
        )
        result = get_structured_output(SearchQueries, prompt)
        return result.queries[:5]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _score_single_paper(
        self,
        paper_structure: PaperStructure,
        user_excerpt: str,
        rp: RelatedPaper,
    ) -> RelatedPaperScored:
        """Score a single related paper via structured LLM output."""
        prompt = LIBRARIAN_SCORER.format(
            user_title=paper_structure.title,
            user_main_claim=paper_structure.main_claim,
            user_excerpt=user_excerpt,
            related_title=rp.title,
            related_authors=rp.authors,
            related_abstract=rp.abstract,
            related_source=rp.source,
        )
        return get_structured_output(RelatedPaperScored, prompt)

    @staticmethod
    def _generate_context_summary(
        paper_structure: PaperStructure | None,
        related_papers: List[RelatedPaper],
    ) -> str:
        """Generate a neutral context summary from related papers."""
        if not related_papers:
            return "No related papers found."

        rp_text = "\n\n".join(
            f"- Title: {rp.title}\n  Authors: {rp.authors}\n  Abstract: {rp.abstract[:300]}"
            for rp in related_papers[:15]
        )

        title = paper_structure.title if paper_structure else "Unknown"
        main_claim = paper_structure.main_claim if paper_structure else ""

        prompt = LIBRARIAN_CONTEXT.format(
            user_title=title,
            user_main_claim=main_claim,
            related_papers_text=rp_text,
        )
        return invoke_text(prompt)
