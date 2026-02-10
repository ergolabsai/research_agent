"""
Pipeline API routes.

Endpoints for submitting papers for validation and retrieving results.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

from app.security import get_current_user_id
from app.services.pipeline_service import (
    create_job,
    get_job,
    list_jobs,
    run_pipeline_async,
    JobStatus,
    PipelineJob,
)
from advisor_pipeline.database import Database
from advisor_pipeline.models.schemas import ValidationResult

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


class ValidationResultResponse(BaseModel):
    paper_id: str
    confidence_score: float
    overall_assessment: str
    step_count: int


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

    job = create_job(paper_id=paper_id, title=request.title)

    background_tasks.add_task(
        run_pipeline_async,
        job_id=job.job_id,
        paper_id=paper_id,
        paper_text=request.paper_text,
        title=request.title,
        figures=request.figures,
        authors=request.authors,
        abstract=request.abstract or "",
        bibliography=request.bibliography,
    )

    return JobResponse(
        job_id=job.job_id,
        paper_id=paper_id,
        title=request.title,
        status=job.status.value,
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
        status=job.status.value,
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
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == JobStatus.PENDING or job.status == JobStatus.RUNNING:
        raise HTTPException(status_code=202, detail="Job still in progress")

    if job.status == JobStatus.FAILED:
        raise HTTPException(status_code=500, detail=f"Job failed: {job.error}")

    if not job.result:
        raise HTTPException(status_code=500, detail="No results available")

    return job.result.model_dump()


@router.get("/history/{paper_id}")
async def get_paper_history(
    paper_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Get all validation results for a paper from MongoDB."""
    try:
        db = Database()
        db.connect()
        validations = db.get_all_validations(paper_id)
        db.disconnect()

        return [v.model_dump() for v in validations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_all_jobs(
    user_id: int = Depends(get_current_user_id),
):
    """List all validation jobs."""
    jobs = list_jobs()
    return [
        JobResponse(
            job_id=j.job_id,
            paper_id=j.paper_id,
            title=j.title,
            status=j.status.value,
            current_step=j.current_step,
            total_steps=j.total_steps,
            step_name=j.step_name,
            error=j.error,
        )
        for j in jobs
    ]
