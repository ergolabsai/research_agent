# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Legacy-wrapping JobStore adapter.

During MIGRATION step 2, only `create()` is wired up — the read-side endpoints
(/status, /results, /graph, ...) still call the legacy `pipeline_service` helpers
directly. The remaining methods raise NotImplementedError; they fill in when the
read-side routes migrate to use-cases (GetJob, ListJobs, GetStepLogs).
"""

from sqlmodel import Session

from app.models import PipelineJob
from core.contracts.auth import Principal
from core.contracts.jobs import Job, JobId, JobPage, JobStatus, StepLog
from core.contracts.validation import ValidationResult


class LegacyJobStore:
    """JobStore backed by the existing SQLite `pipeline_job` table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def create(self, job: Job) -> None:
        row = PipelineJob(
            job_id=job.id,
            user_id=job.user_id,
            paper_id=job.paper_id,
            title=job.title,
            status=job.status.value,
            current_step=job.current_step,
            total_steps=job.total_steps,
            step_name=job.current_step_name or "",
            created_at=job.created_at,
        )
        self._session.add(row)
        self._session.commit()

    async def get(self, job_id: JobId) -> Job | None:
        raise NotImplementedError("Read-side migrates in a later step (GetJob use case).")

    async def list_for(
        self,
        principal: Principal,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> JobPage:
        raise NotImplementedError("Read-side migrates in a later step (ListJobs use case).")

    async def update_status(
        self,
        job_id: JobId,
        status: JobStatus,
        *,
        error: str | None = None,
    ) -> None:
        raise NotImplementedError(
            "Status updates still flow through legacy run_pipeline_async. "
            "Wired when the orchestrator moves into core."
        )

    async def update_progress(
        self,
        job_id: JobId,
        current_step: int,
        step_name: str,
    ) -> None:
        raise NotImplementedError(
            "Progress updates still flow through legacy run_pipeline_async."
        )

    async def save_step_log(self, log: StepLog) -> None:
        raise NotImplementedError(
            "Step logs still flow through legacy run_pipeline_async."
        )

    async def list_step_logs(self, job_id: JobId) -> list[StepLog]:
        raise NotImplementedError("Read-side migrates in a later step (GetStepLogs).")

    async def get_step_log(self, job_id: JobId, step_name: str) -> StepLog | None:
        raise NotImplementedError("Read-side migrates in a later step (GetStepLogs).")

    async def save_result(
        self,
        job_id: JobId,
        result: ValidationResult,
        graph_json: str,
    ) -> None:
        raise NotImplementedError(
            "Result persistence still flows through legacy run_pipeline_async."
        )
