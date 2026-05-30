# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Legacy-wrapping PipelineRunner adapter.

Translates the core `Paper` contract into the kwarg shape expected by
`pipeline_service.run_pipeline_async`, schedules it as a background asyncio task,
and returns immediately. Disappears in MIGRATION step 3 when the orchestrator
moves into `core/services/`.
"""

import asyncio
import json
from typing import Any

from sqlmodel import Session, select

from advisor_pipeline.orchestrator import AdvisorOrchestrator
from app.models import PipelineJob
from app.security import engine
from app.services.pipeline_service import run_pipeline_async
from core.contracts.auth import Principal
from core.contracts.jobs import Job
from core.contracts.paper import FigureRef, Paper


class LegacyPipelineRunner:
    """Fires the legacy orchestrator via `pipeline_service.run_pipeline_async`."""

    def __init__(self, orchestrator: AdvisorOrchestrator):
        self._orchestrator = orchestrator

    async def submit(self, job: Job, paper: Paper, principal: Principal) -> None:
        legacy_figures = _figures_to_legacy_dict(paper.figures)

        # Backfill paper-context columns that the legacy /figures endpoint reads
        # off PipelineJob. JobStore.create only writes the job-state columns.
        _backfill_paper_context(
            job_id=job.id,
            paper_text=paper.text,
            bibliography=paper.bibliography,
            figures=legacy_figures,
        )

        asyncio.create_task(
            run_pipeline_async(
                orchestrator=self._orchestrator,
                job_id=job.id,
                paper_id=job.paper_id,
                paper_text=paper.text,
                title=job.title,
                user_id=int(job.user_id),
                figures=legacy_figures or None,
                authors=list(paper.authors) if paper.authors else None,
                abstract=paper.abstract or "",
                bibliography=paper.bibliography,
            )
        )


def _figures_to_legacy_dict(figures: list[FigureRef]) -> dict[str, dict[str, Any]]:
    """Convert FigureRef list to the legacy {name: {submitted, predicted}} shape."""
    out: dict[str, dict[str, Any]] = {}
    for ref in figures:
        entry: dict[str, Any] = {
            "submitted": {
                "object_key": ref.submitted_storage_key,
                "media_type": ref.submitted_content_type,
            }
        }
        if ref.predicted_storage_key:
            entry["predicted"] = {
                "object_key": ref.predicted_storage_key,
                "media_type": ref.predicted_content_type,
            }
        out[ref.name] = entry
    return out


def _backfill_paper_context(
    *,
    job_id: str,
    paper_text: str,
    bibliography: dict[str, str] | None,
    figures: dict[str, dict[str, Any]],
) -> None:
    """Populate paper_text / figures_json / bibliography_json on the PipelineJob row.

    These columns are written by legacy `create_job` today; LegacyJobStore.create
    only writes the job-state columns to keep the JobStore port surface narrow.
    """
    with Session(engine) as session:
        row = session.exec(select(PipelineJob).where(PipelineJob.job_id == job_id)).first()
        if row is None:
            return
        row.paper_text = paper_text
        if figures:
            row.figures_json = json.dumps(figures)
        if bibliography:
            row.bibliography_json = bibliography
        session.commit()
