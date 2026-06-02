# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Librarian unit tests against fake LLMClient + PaperIndex."""

import pandas as pd

from core.services.librarian import Librarian
from core.contracts.validation import (
    LogicalStep,
    PaperStructure,
    RelatedPaper,
    RelatedPaperScored,
    SearchQueries,
)
from tests.services.conftest import FakeLLMClient, FakePaperIndex


def _paper_structure() -> PaperStructure:
    return PaperStructure(
        title="Ultrafast isomerization",
        main_claim="Vibrational coherence drives the reaction.",
        logical_steps=[
            LogicalStep(
                step_number=1,
                description="Coherence persists past 100fs",
                section="Results",
                depends_on=[],
            )
        ],
    )


def _vector_hit_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": "arxiv:1234.5678",
                "title": "Vibrational coherence in retinal",
                "authors": "Smith, Jones",
                "abstract": "We observe coherent oscillations...",
            }
        ]
    )


def test_gather_papers_runs_vector_search_per_crafted_query():
    structure = _paper_structure()
    llm = FakeLLMClient(
        structured_responses={
            "SearchQueries": [SearchQueries(queries=["coherence retinal", "vibrational dynamics"])],
        },
        text_responses=["context summary"],
    )
    paper_index = FakePaperIndex(vector_results=[_vector_hit_df(), _vector_hit_df()])

    librarian = Librarian(llm=llm, paper_index=paper_index)
    result = librarian.gather_papers(
        paper_text="paper body" * 200,
        bibliography={},
        paper_structure=structure,
    )

    assert result.search_queries == ["coherence retinal", "vibrational dynamics"]
    # One vector_search per crafted query
    assert len(paper_index.vector_calls) == 2
    assert paper_index.vector_calls[0] == ("coherence retinal", 5)
    # Dedup by paper_id — both DFs return the same arxiv id, so we get one paper
    assert len(result.related_papers) == 1
    assert result.context_summary == "context summary"


def test_score_papers_assigns_scores_from_llm():
    llm = FakeLLMClient(
        structured_responses={
            "RelatedPaperScored": [
                RelatedPaperScored(
                    relevancy_score=0.8,
                    relevancy_reasoning="overlapping methodology",
                    convergence_score=0.5,
                    convergence_reasoning="supports main claim",
                )
            ],
        },
    )
    librarian = Librarian(llm=llm, paper_index=FakePaperIndex())

    rp = RelatedPaper(
        paper_id="arxiv:1234.5678",
        title="A related paper",
        authors="X et al",
        abstract="abstract",
        source="lancedb_vector",
    )
    out = librarian.score_papers(
        paper_text="paper body",
        paper_structure=_paper_structure(),
        related_papers=[rp],
    )

    assert len(out) == 1
    assert out[0].relevancy_score == 0.8
    assert out[0].convergence_score == 0.5
    assert out[0].paper_id == "arxiv:1234.5678"


def test_find_cited_paper_uses_fts_first():
    structure = _paper_structure()
    llm = FakeLLMClient(
        structured_responses={
            "SearchQueries": [SearchQueries(queries=[])],
        },
        text_responses=["ctx"],
    )
    paper_index = FakePaperIndex(
        fts_results=[
            pd.DataFrame(
                [
                    {
                        "id": "cited-1",
                        "title": "Cited paper title",
                        "authors": "Cited et al",
                        "abstract": "cited abstract",
                    }
                ]
            )
        ]
    )

    librarian = Librarian(llm=llm, paper_index=paper_index)
    result = librarian.gather_papers(
        paper_text="x",
        bibliography={"ref1": 'Author. "Cited paper title". Journal. 2020.'},
        paper_structure=structure,
    )

    assert paper_index.fts_calls, "FTS must be tried first for cited papers"
    assert any(rp.paper_id == "cited-1" for rp in result.related_papers)
