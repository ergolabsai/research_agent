# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Service layer wrapping the AdvisorOrchestrator for use from the FastAPI backend.

Manages pipeline lifecycle, job tracking (persistent in SQLite), and async execution.
Each pipeline step's full agent output is logged to PipelineStepLog for transparency.
"""

import asyncio
import base64
import json
import logging
import mimetypes
import time
import uuid
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional

import networkx as nx
from sqlmodel import Session, select
import httpx

logger = logging.getLogger(__name__)

from advisor_pipeline.orchestrator import AdvisorOrchestrator
from advisor_pipeline.models.paper_graph import (
    build_graph_from_validation,
    get_contradicted_steps,
    get_invalid_math,
    get_librarian_statistics,
    get_related_papers,
    get_high_impact_papers,
    get_steps_with_no_evidence,
    get_steps_with_no_evaluation,
    get_figure_confirmation_counts,
    get_nodes_by_type,
    save_graph,
)
from advisor_pipeline.models.schemas import ValidationResult
from app.models import PipelineJob, PipelineStepLog
from app.security import engine
from app.storage import get_object_bytes
from app.time import now


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# In-memory graph cache (NetworkX graphs aren't serializable to SQLite)
_graphs: dict[str, nx.DiGraph] = {}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_session() -> Session:
    return Session(engine)


def get_job(job_id: str) -> Optional[PipelineJob]:
    with _get_session() as session:
        stmt = select(PipelineJob).where(PipelineJob.job_id == job_id)
        job = session.exec(stmt).first()
        if job:
            session.expunge(job)
        return job


def get_job_graph(job_id: str) -> Optional[nx.DiGraph]:
    """Return the paper graph for a completed job, building from stored JSON if needed."""
    if job_id in _graphs:
        return _graphs[job_id]

    job = get_job(job_id)
    if job and job.graph_json:
        G = nx.node_link_graph(json.loads(job.graph_json))
        _graphs[job_id] = G
        return G

    if job and job.result_json:
        result = ValidationResult.model_validate_json(job.result_json)
        G = build_graph_from_validation(result)
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
    lib_stats = get_librarian_statistics(G)
    fig_counts = get_figure_confirmation_counts(G)
    steps_no_evidence = get_steps_with_no_evidence(G)
    steps_no_evaluation = get_steps_with_no_evaluation(G)
    related = get_related_papers(G)
    high_impact = get_high_impact_papers(G)

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
        "librarian_statistics": lib_stats,
        "figure_confirmation_counts": fig_counts,
        "related_papers": [
            {
                "paper_id": r.get("paper_id"),
                "title": r.get("title"),
                "source": r.get("source"),
                "relevancy_score": r.get("relevancy_score"),
                "convergence_score": r.get("convergence_score"),
                "convergence_reasoning": r.get("convergence_reasoning", ""),
            }
            for r in related
        ],
        "high_impact_papers": [
            {
                "paper_id": r.get("paper_id"),
                "title": r.get("title"),
                "relevancy_score": r.get("relevancy_score"),
                "convergence_score": r.get("convergence_score"),
                "convergence_reasoning": r.get("convergence_reasoning", ""),
            }
            for r in high_impact
        ],
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
            "related_papers": len(get_nodes_by_type(G, "related_paper")),
        },
    }


def get_step_logs(job_id: str) -> list[PipelineStepLog]:
    """Return all step logs for a job, ordered by step number."""
    with _get_session() as session:
        stmt = (
            select(PipelineStepLog)
            .where(PipelineStepLog.job_id == job_id)
            .order_by(PipelineStepLog.step_number)
        )
        logs = session.exec(stmt).all()
        for log in logs:
            session.expunge(log)
        return list(logs)


def get_step_log(job_id: str, step_name: str) -> Optional[PipelineStepLog]:
    """Return a single step log by job_id and step_name."""
    with _get_session() as session:
        stmt = (
            select(PipelineStepLog)
            .where(PipelineStepLog.job_id == job_id, PipelineStepLog.step_name == step_name)
        )
        log = session.exec(stmt).first()
        if log:
            session.expunge(log)
        return log


def list_jobs(user_id: int = None) -> list[PipelineJob]:
    with _get_session() as session:
        stmt = select(PipelineJob).order_by(PipelineJob.created_at.desc())
        if user_id is not None:
            stmt = stmt.where(PipelineJob.user_id == user_id)
        jobs = session.exec(stmt).all()
        for job in jobs:
            session.expunge(job)
        return list(jobs)


# ---------------------------------------------------------------------------
# Step logging callback
# ---------------------------------------------------------------------------

# Maps orchestrator node names to human-readable names and step numbers
STEP_MAP = {
    "make_context": ("Context Enrichment", 1),
    "gather_papers": ("Librarian — Gather Papers", 2),
    "map_logic": ("Logic Mapping", 3),
    "find_evidence": ("Evidence Finding", 4),
    "evaluate_figures": ("Figure Evaluation", 5),
    "evaluate_math": ("Math Evaluation", 6),
    "score_papers": ("Librarian — Score Papers", 7),
    "compile_results": ("Compile Results", 8),
}


def _log_step(job_id: str, node_name: str, output: dict, prompts: list[str] | None = None,
              duration: float = 0.0, status: str = "completed"):
    """Persist a step's output to SQLite."""
    step_label, step_num = STEP_MAP.get(node_name, (node_name, 0))

    with _get_session() as session:
        # Update job progress
        stmt = select(PipelineJob).where(PipelineJob.job_id == job_id)
        job = session.exec(stmt).first()
        if job:
            job.current_step = step_num
            job.step_name = step_label

        log = PipelineStepLog(
            job_id=job_id,
            step_name=node_name,
            step_number=step_num,
            status=status,
            output_json=json.dumps(output, default=str),
            prompts_json=json.dumps(prompts, default=str) if prompts else None,
            started_at=now(),
            completed_at=now(),
            duration_seconds=duration,
        )
        session.add(log)
        session.commit()


def _extract_step_output(node_name: str, state_update: dict) -> dict:
    """Extract the meaningful output from a node's state update for logging."""
    if node_name == "make_context":
        text = state_update.get("paper_text", "")
        # Just log the additional context portion
        marker = "--- Additional Context ---"
        if marker in text:
            return {"enriched_context": text.split(marker, 1)[1].strip()}
        return {"enriched_context": text[-2000:] if len(text) > 2000 else text}

    elif node_name == "gather_papers":
        lib_result = state_update.get("librarian_result")
        if lib_result and hasattr(lib_result, "model_dump"):
            lib_data = lib_result.model_dump()
        elif isinstance(lib_result, dict):
            lib_data = lib_result
        else:
            lib_data = {}
        return {
            "search_queries": lib_data.get("search_queries", []),
            "related_papers": [
                {
                    "paper_id": rp.get("paper_id", ""),
                    "title": rp.get("title", ""),
                    "authors": rp.get("authors", ""),
                    "source": rp.get("source", ""),
                    "abstract": rp.get("abstract", "")[:500],
                }
                for rp in lib_data.get("related_papers", [])
            ],
            "context_summary": lib_data.get("context_summary", ""),
            "paper_count": len(lib_data.get("related_papers", [])),
        }

    elif node_name == "map_logic":
        ps = state_update.get("paper_structure")
        if ps and hasattr(ps, "model_dump"):
            return ps.model_dump()
        return {"paper_structure": ps} if ps else {}

    elif node_name == "find_evidence":
        evidence_list = state_update.get("step_evidence", [])
        return {
            "step_evidence": [
                se.model_dump() if hasattr(se, "model_dump") else se
                for se in evidence_list
            ],
            "total_evidence_count": sum(
                len(se.evidence_list) if hasattr(se, "evidence_list") else 0
                for se in evidence_list
            ),
        }

    elif node_name == "evaluate_figures":
        evals = state_update.get("figure_evaluations", [])
        return {
            "figure_evaluations": [
                fe.model_dump() if hasattr(fe, "model_dump") else fe
                for fe in evals
            ],
            "figure_count": len(evals),
        }

    elif node_name == "evaluate_math":
        evals = state_update.get("math_evaluations", [])
        return {
            "math_evaluations": [
                me.model_dump() if hasattr(me, "model_dump") else me
                for me in evals
            ],
            "math_count": len(evals),
        }

    elif node_name == "score_papers":
        lib_result = state_update.get("librarian_result")
        if lib_result and hasattr(lib_result, "model_dump"):
            lib_data = lib_result.model_dump()
        elif isinstance(lib_result, dict):
            lib_data = lib_result
        else:
            lib_data = {}
        return {
            "scored_papers": [
                {
                    "paper_id": rp.get("paper_id", ""),
                    "title": rp.get("title", ""),
                    "source": rp.get("source", ""),
                    "relevancy_score": rp.get("relevancy_score", 0),
                    "relevancy_reasoning": rp.get("relevancy_reasoning", ""),
                    "convergence_score": rp.get("convergence_score", 0),
                    "convergence_reasoning": rp.get("convergence_reasoning", ""),
                }
                for rp in lib_data.get("related_papers", [])
            ],
            "paper_count": len(lib_data.get("related_papers", [])),
        }

    elif node_name == "compile_results":
        result = state_update.get("validation_result")
        if result and hasattr(result, "model_dump"):
            result_data = result.model_dump()
        elif isinstance(result, dict):
            result_data = result
        else:
            result_data = {}
        return {
            "confidence_score": result_data.get("confidence_score"),
            "overall_assessment": result_data.get("overall_assessment"),
        }

    return state_update


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

async def run_pipeline_async(
    job_id: str,
    paper_id: str,
    paper_text: str,
    title: str,
    user_id: int,
    figures: dict[str, dict] | None = None,
    authors: list[str] | None = None,
    abstract: str = "",
    bibliography: dict[str, str] | None = None,
) -> None:
    """Run the pipeline in a background thread (it's CPU/IO bound)."""
    # Mark job as running
    with _get_session() as session:
        stmt = select(PipelineJob).where(PipelineJob.job_id == job_id)
        job = session.exec(stmt).first()
        if job:
            job.status = JobStatus.RUNNING.value
            session.commit()

    def _run():
        try:
            logger.info("Pipeline job %s started for paper %s", job_id, paper_id)
            orchestrator = AdvisorOrchestrator()
            hydrated_figures = _hydrate_figure_payloads(figures or {})

            # Create step callback for logging
            def on_step_complete(node_name: str, state_update: dict, duration: float):
                try:
                    output = _extract_step_output(node_name, state_update)
                    _log_step(job_id, node_name, output, duration=duration)
                except Exception as log_err:
                    logger.warning("Failed to log step %s: %s", node_name, log_err)

            result = orchestrator.run(
                paper_text=paper_text,
                figures=hydrated_figures,
                paper_bib=bibliography,
                on_step_complete=on_step_complete,
            )
            result.paper_id = paper_id

            # Build and cache the graph
            G = build_graph_from_validation(result)
            _graphs[job_id] = G

            # Persist final results
            with _get_session() as session:
                stmt = select(PipelineJob).where(PipelineJob.job_id == job_id)
                job = session.exec(stmt).first()
                if job:
                    job.result_json = result.model_dump_json()
                    job.graph_json = json.dumps(nx.node_link_data(G), default=str)
                    job.status = JobStatus.COMPLETED.value
                    job.completed_at = now()
                    session.commit()

            logger.info("Pipeline job %s completed successfully", job_id)

        except Exception as e:
            logger.error("Pipeline job %s failed: %s", job_id, e, exc_info=True)
            with _get_session() as session:
                stmt = select(PipelineJob).where(PipelineJob.job_id == job_id)
                job = session.exec(stmt).first()
                if job:
                    job.status = JobStatus.FAILED.value
                    job.error = str(e)
                    job.completed_at = now()
                    session.commit()

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run)


def create_job(
    paper_id: str,
    title: str,
    user_id: int,
    paper_text: str = "",
    bibliography: dict | None = None,
    figures: dict | None = None,
) -> PipelineJob:
    job_id = str(uuid.uuid4())
    with _get_session() as session:
        job = PipelineJob(
            job_id=job_id,
            user_id=user_id,
            paper_id=paper_id,
            title=title,
            paper_text=paper_text,
            bibliography_json=json.dumps(bibliography) if bibliography else None,
            figures_json=json.dumps(figures) if figures else None,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        session.expunge(job)
    return job


def _hydrate_figure_payloads(figure_refs: dict[str, dict]) -> dict[str, dict[str, str]]:
    """Resolve figure refs into base64 payloads for submitted/predicted images."""
    hydrated: dict[str, dict[str, str]] = {}
    for figure_name, payload in figure_refs.items():
        try:
            submitted_payload = payload.get("submitted") if isinstance(payload.get("submitted"), dict) else payload
            predicted_payload = payload.get("predicted") if isinstance(payload.get("predicted"), dict) else None

            resolved_submitted = _resolve_single_figure(submitted_payload)
            if not resolved_submitted:
                continue

            combined = {
                "data": resolved_submitted["data"],
                "media_type": resolved_submitted["media_type"],
            }

            resolved_predicted = _resolve_single_figure(predicted_payload)
            if resolved_predicted:
                combined["predicted_data"] = resolved_predicted["data"]
                combined["predicted_media_type"] = resolved_predicted["media_type"]

            hydrated[figure_name] = combined
        except Exception as exc:
            logger.warning("Failed to hydrate figure '%s': %s", figure_name, exc)
    return hydrated


def _resolve_single_figure(payload: dict) -> Optional[dict[str, str]]:
    if not isinstance(payload, dict):
        return None

    # Already in orchestrator-ready shape.
    if payload.get("data") and payload.get("media_type"):
        return {
            "data": payload["data"],
            "media_type": payload["media_type"],
        }

    media_type = payload.get("media_type")
    object_key = payload.get("object_key")
    image_bytes: Optional[bytes] = None

    if object_key:
        image_bytes = get_object_bytes(object_key)
        media_type = media_type or mimetypes.guess_type(object_key)[0] or "image/jpeg"
    else:
        url = payload.get("url") or payload.get("path")
        if isinstance(url, str) and url.startswith("/static/attachments/"):
            inferred_key = url[len("/static/attachments/"):]
            image_bytes = get_object_bytes(inferred_key)
            media_type = media_type or mimetypes.guess_type(inferred_key)[0] or "image/jpeg"
        elif isinstance(url, str) and url:
            response = httpx.get(url, timeout=20.0)
            response.raise_for_status()
            image_bytes = response.content
            media_type = media_type or response.headers.get("content-type") or "image/jpeg"

    if not image_bytes:
        return None

    return {
        "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
        "media_type": media_type or "image/jpeg",
    }
