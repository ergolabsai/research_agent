# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

import uuid
from datetime import datetime, timezone

from core.contracts import authz
from core.contracts.auth import Principal
from core.contracts.authz import Permission
from core.contracts.jobs import Job, JobId
from core.contracts.validation import ValidatePaperRequest, ValidatePaperResponse
from core.ports.job_store import JobStore
from core.ports.pipeline_runner import PipelineRunner


class ValidatePaper:
    """
    Submit a paper for validation.

    Creates a job record and fires the pipeline runner. Returns immediately with
    the new Job; progress and final results are written through `JobStore` by
    the runner. Callers poll for status via a separate use case.
    """

    def __init__(self, job_store: JobStore, pipeline_runner: PipelineRunner) -> None:
        self._job_store = job_store
        self._pipeline_runner = pipeline_runner

    async def execute(
        self, principal: Principal, request: ValidatePaperRequest
    ) -> ValidatePaperResponse:
        authz.require(principal, Permission.VALIDATE_PAPER)

        now = datetime.now(timezone.utc)
        job = Job(
            id=JobId(str(uuid.uuid4())),
            user_id=principal.user_id,
            paper_id=request.paper_id or str(uuid.uuid4()),
            title=request.paper.title or "Untitled",
            created_at=now,
            updated_at=now,
        )

        await self._job_store.create(job)
        await self._pipeline_runner.submit(job, request.paper, principal)

        return ValidatePaperResponse(job=job)
