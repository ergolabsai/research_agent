# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""JobStore port. See ports/0004."""

from typing import Protocol, runtime_checkable

from core.contracts.auth import Principal
from core.contracts.jobs import Job, JobId, JobPage, JobStatus, StepLog
from core.contracts.validation import ValidationResult


@runtime_checkable
class JobStore(Protocol):
    async def create(self, job: Job) -> None: ...

    async def get(self, job_id: JobId) -> Job | None: ...

    async def list_for(
        self,
        principal: Principal,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> JobPage: ...

    async def update_status(
        self,
        job_id: JobId,
        status: JobStatus,
        *,
        error: str | None = None,
    ) -> None: ...

    async def update_progress(
        self,
        job_id: JobId,
        current_step: int,
        step_name: str,
    ) -> None: ...

    async def save_step_log(self, log: StepLog) -> None: ...

    async def list_step_logs(self, job_id: JobId) -> list[StepLog]: ...

    async def get_step_log(self, job_id: JobId, step_name: str) -> StepLog | None: ...

    async def save_result(
        self,
        job_id: JobId,
        result: ValidationResult,
        graph_json: str,
    ) -> None: ...
