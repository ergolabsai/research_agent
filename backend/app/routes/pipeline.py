# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Pipeline API routes.

Endpoints for submitting papers for validation, retrieving results,
and inspecting per-step agent outputs for transparency.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

import json
import networkx as nx

from app.security import get_current_user_id
from app.services.pipeline_service import (
    create_job,
    get_graph_analysis,
    get_job,
    get_job_graph,
    get_step_log,
    get_step_logs,
    list_jobs,
    run_pipeline_async,
    JobStatus,
)
router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


# --- Request / Response Models ---


class ValidateRequest(BaseModel):
    paper_text: str = Field(..., description="Full text of the paper to validate")
    title: str = Field(..., description="Paper title")
    paper_id: Optional[str] = Field(
        default=None, description="Optional paper ID (generated if omitted)"
    )
    authors: Optional[list[str]] = None
    abstract: Optional[str] = ""
    bibliography: Optional[dict[str, str]] = None
    figures: Optional[dict[str, str]] = None


class JobResponse(BaseModel):
    job_id: str
    paper_id: str
    title: str
    status: str
    current_step: int
    total_steps: int
    step_name: str
    error: Optional[str] = None


class StepLogResponse(BaseModel):
    step_name: str
    step_number: int
    status: str
    output: Optional[dict] = None
    prompts: Optional[list] = None
    duration_seconds: Optional[float] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# --- Endpoints ---


@router.post("/validate", response_model=JobResponse)
async def submit_validation(
    request: ValidateRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
):
    """Submit a paper for validation. Returns a job ID to poll for status."""
    import uuid

    paper_id = request.paper_id or str(uuid.uuid4())

    job = create_job(
        paper_id=paper_id,
        title=request.title,
        user_id=user_id,
        paper_text=request.paper_text,
        bibliography=request.bibliography,
        figures=request.figures,
    )

    background_tasks.add_task(
        run_pipeline_async,
        job_id=job.job_id,
        paper_id=paper_id,
        paper_text=request.paper_text,
        title=request.title,
        user_id=user_id,
        figures=request.figures,
        authors=request.authors,
        abstract=request.abstract or "",
        bibliography=request.bibliography,
    )

    return JobResponse(
        job_id=job.job_id,
        paper_id=paper_id,
        title=request.title,
        status=job.status,
        current_step=job.current_step,
        total_steps=job.total_steps,
        step_name="Queued",
    )


@router.get("/status/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Check the status of a validation job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        job_id=job.job_id,
        paper_id=job.paper_id,
        title=job.title,
        status=job.status,
        current_step=job.current_step,
        total_steps=job.total_steps,
        step_name=job.step_name,
        error=job.error,
    )


@router.get("/results/{job_id}")
async def get_job_results(
    job_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Get the full validation results for a completed job."""
    job = _require_completed_job(job_id)
    if not job.result_json:
        raise HTTPException(status_code=500, detail="No results available")
    return json.loads(job.result_json)


@router.get("/graph/{job_id}")
async def get_job_graph_data(
    job_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Get the paper graph for a completed job in node-link format."""
    _require_completed_job(job_id)
    G = get_job_graph(job_id)
    if G is None:
        raise HTTPException(status_code=500, detail="Graph not available")
    return nx.node_link_data(G)


@router.get("/analysis/{job_id}")
async def get_job_analysis(
    job_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Get graph-based analysis for a completed job."""
    _require_completed_job(job_id)
    analysis = get_graph_analysis(job_id)
    if analysis is None:
        raise HTTPException(status_code=500, detail="Analysis not available")
    return analysis


@router.get("/steps/{job_id}", response_model=list[StepLogResponse])
async def get_job_steps(
    job_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Get all step logs for a job — full agent outputs for transparency."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logs = get_step_logs(job_id)
    return [
        StepLogResponse(
            step_name=log.step_name,
            step_number=log.step_number,
            status=log.status,
            output=json.loads(log.output_json) if log.output_json else None,
            prompts=json.loads(log.prompts_json) if log.prompts_json else None,
            duration_seconds=log.duration_seconds,
            started_at=str(log.started_at) if log.started_at else None,
            completed_at=str(log.completed_at) if log.completed_at else None,
        )
        for log in logs
    ]


@router.get("/steps/{job_id}/{step_name}", response_model=StepLogResponse)
async def get_job_step(
    job_id: str,
    step_name: str,
    user_id: int = Depends(get_current_user_id),
):
    """Get a single step's output by name (e.g., 'gather_papers', 'score_papers')."""
    log = get_step_log(job_id, step_name)
    if not log:
        raise HTTPException(status_code=404, detail=f"Step '{step_name}' not found for this job")

    return StepLogResponse(
        step_name=log.step_name,
        step_number=log.step_number,
        status=log.status,
        output=json.loads(log.output_json) if log.output_json else None,
        prompts=json.loads(log.prompts_json) if log.prompts_json else None,
        duration_seconds=log.duration_seconds,
        started_at=str(log.started_at) if log.started_at else None,
        completed_at=str(log.completed_at) if log.completed_at else None,
    )


@router.get("/jobs")
async def list_all_jobs(
    user_id: int = Depends(get_current_user_id),
):
    """List all validation jobs for the current user."""
    jobs = list_jobs(user_id=user_id)
    return [
        JobResponse(
            job_id=j.job_id,
            paper_id=j.paper_id,
            title=j.title,
            status=j.status,
            current_step=j.current_step,
            total_steps=j.total_steps,
            step_name=j.step_name,
            error=j.error,
        )
        for j in jobs
    ]


# --- Helpers ---


def _require_completed_job(job_id: str):
    """Validate that a job exists, is completed, and has results."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in (JobStatus.PENDING.value, JobStatus.RUNNING.value):
        raise HTTPException(status_code=202, detail="Job still in progress")

    if job.status == JobStatus.FAILED.value:
        raise HTTPException(status_code=500, detail=f"Job failed: {job.error}")

    if not job.result_json:
        raise HTTPException(status_code=500, detail="No results available")

    return job
