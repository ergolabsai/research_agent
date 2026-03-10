"""
Service layer wrapping the AdvisorOrchestrator for use from the FastAPI backend.

Manages pipeline lifecycle, job tracking, and async execution.
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

import networkx as nx
from pydantic import BaseModel, Field

from advisor_pipeline.orchestrator import AdvisorOrchestrator
from advisor_pipeline.models.paper_graph import (
    build_graph_from_validation,
    get_contradicted_steps,
    get_invalid_math,
    get_citation_statistics,
    get_steps_with_no_evidence,
    get_steps_with_no_evaluation,
    get_figure_confirmation_counts,
    get_nodes_by_type,
    save_graph,
)
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

    class Config:
        arbitrary_types_allowed = True


# In-memory job store (sufficient for single-server deployment)
_jobs: dict[str, PipelineJob] = {}
# Separate store for graphs (not serializable by Pydantic)
_graphs: dict[str, nx.DiGraph] = {}


def get_job(job_id: str) -> Optional[PipelineJob]:
    return _jobs.get(job_id)


def get_job_graph(job_id: str) -> Optional[nx.DiGraph]:
    """Return the paper graph for a completed job, building from result if needed."""
    if job_id in _graphs:
        return _graphs[job_id]
    job = _jobs.get(job_id)
    if job and job.result:
        G = build_graph_from_validation(job.result)
        _graphs[job_id] = G
        return G
    return None


def get_graph_analysis(job_id: str) -> Optional[dict]:
    """Return graph-based analysis for a completed job."""
    G = get_job_graph(job_id)
    if G is None:
        return None

    contradictions = get_contradicted_steps(G)
    invalid_math = get_invalid_math(G)
    cit_stats = get_citation_statistics(G)
    fig_counts = get_figure_confirmation_counts(G)
    steps_no_evidence = get_steps_with_no_evidence(G)
    steps_no_evaluation = get_steps_with_no_evaluation(G)

    return {
        "contradicted_steps": [
            {
                "step_number": c["step"].get("step_number"),
                "step_description": c["step"].get("description"),
                "figure": c["figure"],
                "contradictions": c["contradictions"],
            }
            for c in contradictions
        ],
        "invalid_math": [
            {
                "equation_reference": m.get("equation_reference"),
                "details": m.get("details"),
            }
            for m in invalid_math
        ],
        "citation_statistics": cit_stats,
        "figure_confirmation_counts": fig_counts,
        "steps_without_evidence": [
            {"step_number": s["step_number"], "description": s["description"]}
            for s in steps_no_evidence
        ],
        "steps_without_evaluation": [
            {"step_number": s["step_number"], "description": s["description"]}
            for s in steps_no_evaluation
        ],
        "node_counts": {
            "steps": len(get_nodes_by_type(G, "step")),
            "evidence": len(get_nodes_by_type(G, "evidence")),
            "figures": len(get_nodes_by_type(G, "figure")),
            "math": len(get_nodes_by_type(G, "math")),
            "citations": len(get_nodes_by_type(G, "citation")),
        },
    }


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
            orchestrator = AdvisorOrchestrator(on_step=_on_step)

            normalized_figures = {
                key: {"path": value} if isinstance(value, str) else value
                for key, value in (figures or {}).items()
            }

            result = orchestrator.run(
                paper_text=paper_text,
                figures=normalized_figures,
                paper_bib=bibliography,
            )
            result.paper_id = paper_id

            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()

            # Build and cache the graph
            _graphs[job_id] = build_graph_from_validation(result)

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
