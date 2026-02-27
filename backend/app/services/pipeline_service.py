"""
Service layer wrapping the AdvisorPipeline for use from the FastAPI backend.

Manages pipeline lifecycle, job tracking, and async execution.
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from advisor_pipeline.pipeline import AdvisorPipeline
from advisor_pipeline.models.schemas import ValidationResult


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineJob(BaseModel):
    job_id: str
    paper_id: str
    title: str
    status: JobStatus = JobStatus.PENDING
    current_step: int = 0
    total_steps: int = 6
    step_name: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[ValidationResult] = None


# In-memory job store (sufficient for single-server deployment)
_jobs: dict[str, PipelineJob] = {}


def get_job(job_id: str) -> Optional[PipelineJob]:
    return _jobs.get(job_id)


def list_jobs(user_id: int = None) -> list[PipelineJob]:
    return list(_jobs.values())


async def run_pipeline_async(
    job_id: str,
    paper_id: str,
    paper_text: str,
    title: str,
    figures: dict[str, str] | None = None,
    authors: list[str] | None = None,
    abstract: str = "",
    bibliography: dict[str, str] | None = None,
) -> None:
    """Run the pipeline in a background thread (it's CPU/IO bound)."""
    job = _jobs[job_id]
    job.status = JobStatus.RUNNING

    def _on_step(step: int, name: str):
        job.current_step = step
        job.step_name = name

    def _run():
        try:
            pipeline = AdvisorPipeline(on_step=_on_step)

            result = pipeline.run(
                paper_id=paper_id,
                paper_text=paper_text,
                title=title,
                figures=figures,
                authors=authors,
                abstract=abstract,
                bibliography=bibliography,
            )

            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run)


def create_job(paper_id: str, title: str) -> PipelineJob:
    job_id = str(uuid.uuid4())
    job = PipelineJob(job_id=job_id, paper_id=paper_id, title=title)
    _jobs[job_id] = job
    return job
