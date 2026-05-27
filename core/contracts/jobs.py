# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Pipeline-job contracts. See ports/0004 (JobStore) and capabilities/validation/README."""

from datetime import datetime
from enum import StrEnum
from typing import Any, NewType

from pydantic import BaseModel

from core.contracts.auth import UserId

JobId = NewType("JobId", str)


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """A validation job. Created on submission; mutated by the orchestrator via JobStore."""

    id: JobId
    user_id: UserId
    paper_id: str
    title: str
    status: JobStatus = JobStatus.PENDING
    current_step: int = 0
    total_steps: int = 8
    current_step_name: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = {"frozen": True}


class StepLog(BaseModel):
    """Per-step output captured during pipeline execution (for transparency)."""

    job_id: JobId
    step_name: str
    step_number: int
    status: JobStatus
    # Agent output payload — schema varies per step; the contract is intentionally untyped here.
    output: dict[str, Any]
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None

    model_config = {"frozen": True}


class JobPage(BaseModel):
    """One page of jobs from JobStore.list_for."""

    jobs: list[Job]
    next_cursor: str | None = None

    model_config = {"frozen": True}
