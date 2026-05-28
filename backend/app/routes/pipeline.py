# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Pipeline API routes.

Endpoints for submitting papers for validation, retrieving results,
and inspecting per-step agent outputs for transparency.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import re

import json
import networkx as nx
from sqlmodel import Session, select

from app.security import get_current_user_id
from app.security import get_session
from app.models import Attachment, Document
from app.storage import get_presigned_url
from app.services.pipeline_service import (
    get_graph_analysis,
    get_job,
    get_job_graph,
    get_step_log,
    get_step_logs,
    list_jobs,
    JobStatus,
)
from composition.container import get_principal, get_validate_paper
from core.contracts.auth import Principal
from core.contracts.errors import Forbidden
from core.contracts.paper import FigureRef, Paper
from core.contracts.validation import ValidatePaperRequest
from core.use_cases.validation.validate_paper import ValidatePaper
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
    document_id: Optional[int] = None
    bibliography: Optional[dict[str, str]] = None
    figures: Optional[dict[str, dict]] = None


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
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_principal),
    use_case: ValidatePaper = Depends(get_validate_paper),
):
    """Submit a paper for validation. Returns a job ID to poll for status."""
    if request.figures:
        figure_refs = _dict_figures_to_refs(request.figures)
    elif request.document_id:
        figure_refs = _build_figure_refs_from_document(
            session=session,
            document_id=request.document_id,
            user_id=int(principal.user_id),
        )
    else:
        figure_refs = []

    paper = Paper(
        text=request.paper_text,
        title=request.title,
        authors=request.authors,
        abstract=request.abstract or None,
        figures=figure_refs,
        bibliography=request.bibliography,
    )

    try:
        result = await use_case.execute(
            principal,
            ValidatePaperRequest(paper=paper, paper_id=request.paper_id),
        )
    except Forbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    job = result.job
    return JobResponse(
        job_id=job.id,
        paper_id=job.paper_id,
        title=job.title,
        status=job.status.value,
        current_step=job.current_step,
        total_steps=job.total_steps,
        step_name=job.current_step_name or "Queued",
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


@router.get("/figures/{job_id}")
async def get_job_figures(
    job_id: str,
    user_id: int = Depends(get_current_user_id),
):
    """Get backend image URLs for figure assets used in a job run."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    refs = json.loads(job.figures_json) if job.figures_json else {}
    assets = []
    for figure_name, payload in refs.items():
        if not isinstance(payload, dict):
            continue

        submitted = payload.get("submitted") if isinstance(payload.get("submitted"), dict) else payload
        predicted = payload.get("predicted") if isinstance(payload.get("predicted"), dict) else None

        submitted_key = submitted.get("object_key") if isinstance(submitted, dict) else None
        predicted_key = predicted.get("object_key") if isinstance(predicted, dict) else None

        assets.append(
            {
                "figure_name": figure_name,
                "submitted": {
                    "filename": (submitted or {}).get("filename")
                    or (Path(submitted_key).name if submitted_key else None),
                    "media_type": (submitted or {}).get("media_type"),
                    "url": get_presigned_url(submitted_key) if submitted_key else None,
                },
                "predicted": {
                    "filename": (predicted or {}).get("filename")
                    or (Path(predicted_key).name if predicted_key else None),
                    "media_type": (predicted or {}).get("media_type"),
                    "url": get_presigned_url(predicted_key) if predicted_key else None,
                },
            }
        )

    return {"job_id": job_id, "figures": assets}


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


def _build_figure_refs_from_document(
    session: Session,
    document_id: int,
    user_id: int,
) -> list[FigureRef]:
    """Build FigureRefs from image attachments on a document.

    Files named like 'predicted'/'expected'/'model' fill the predicted slot;
    everything else fills submitted. If only a predicted image exists for a
    figure, it doubles as the submitted image so the evaluator still has input.
    """
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    attachments = session.exec(
        select(Attachment).where(Attachment.document_id == document_id)
    ).all()

    slots: dict[str, dict[str, dict[str, str]]] = {}
    for idx, attachment in enumerate(attachments, start=1):
        content_type = (attachment.content_type or "").lower()
        if not content_type.startswith("image/"):
            continue

        figure_name = _derive_figure_name(attachment.filename, idx)
        role = _derive_figure_role(attachment.filename)

        entry = slots.setdefault(figure_name, {})
        if role in entry:
            role = "submitted"
        entry[role] = {
            "object_key": attachment.object_key,
            "media_type": attachment.content_type,
        }

    refs: list[FigureRef] = []
    for name, entry in slots.items():
        submitted = entry.get("submitted") or entry.get("predicted")
        if not submitted:
            continue
        predicted = entry.get("predicted") if "submitted" in entry else None
        refs.append(
            FigureRef(
                name=name,
                submitted_storage_key=submitted["object_key"],
                submitted_content_type=submitted["media_type"],
                predicted_storage_key=predicted["object_key"] if predicted else None,
                predicted_content_type=predicted["media_type"] if predicted else None,
            )
        )
    return refs


def _dict_figures_to_refs(figures: dict[str, dict]) -> list[FigureRef]:
    """Convert legacy {name: {submitted, predicted}} request payload to FigureRefs."""
    refs: list[FigureRef] = []
    for name, payload in figures.items():
        if not isinstance(payload, dict):
            continue
        submitted = payload.get("submitted") if isinstance(payload.get("submitted"), dict) else payload
        predicted = payload.get("predicted") if isinstance(payload.get("predicted"), dict) else None
        if not isinstance(submitted, dict) or not submitted.get("object_key"):
            continue
        refs.append(
            FigureRef(
                name=name,
                submitted_storage_key=submitted["object_key"],
                submitted_content_type=submitted.get("media_type") or "image/png",
                predicted_storage_key=predicted.get("object_key") if predicted else None,
                predicted_content_type=(predicted.get("media_type") if predicted else None),
            )
        )
    return refs


def _derive_figure_name(filename: str, index: int) -> str:
    stem = Path(filename).stem
    match = re.search(r"fig(?:ure)?[\s_\-]*(\d+)", stem, flags=re.IGNORECASE)
    if match:
        return f"Figure {match.group(1)}"
    return f"Figure {index}"


def _derive_figure_role(filename: str) -> str:
    """Infer whether an image is submitted (observed) or predicted."""
    stem = Path(filename).stem.lower()
    if any(token in stem for token in ("pred", "predicted", "expected", "model")):
        return "predicted"
    if any(token in stem for token in ("submitted", "observed", "actual", "source")):
        return "submitted"
    return "submitted"
