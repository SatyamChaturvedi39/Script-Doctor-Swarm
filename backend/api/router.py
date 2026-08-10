"""
API router — coverage endpoints.

POST /api/coverage          — upload a screenplay, start pipeline
GET  /api/coverage/{id}/stream — SSE progress stream
GET  /api/coverage/{id}     — fetch completed report (or 202 if pending)
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from api.jobs import create_job, get_job, push_event
from api.schemas import CoverageJobResponse, JobStatusResponse
from parser.extractor import extract_text, estimate_page_count

logger = logging.getLogger("script_doctor.api")
router = APIRouter(prefix="/api")


# ───────────────────────────────────────────────────────────────────────────
# POST /api/coverage — upload and start
# ───────────────────────────────────────────────────────────────────────────

@router.post("/coverage", response_model=CoverageJobResponse)
async def create_coverage(file: UploadFile = File(...)):
    """Accept a .txt or .pdf screenplay and launch the coverage pipeline."""

    # Validate file type
    filename = file.filename or ""
    if not filename.lower().endswith((".txt", ".pdf")):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .pdf screenplay files are accepted.",
        )

    # Read and extract text
    try:
        raw_bytes = await file.read()
        script_text = await asyncio.to_thread(extract_text, raw_bytes, filename)
    except Exception as exc:
        logger.exception("Failed to extract text from %s", filename)
        raise HTTPException(status_code=422, detail=f"Could not parse file: {exc}")

    if len(script_text.strip()) < 100:
        raise HTTPException(
            status_code=422,
            detail="File appears too short to be a screenplay.",
        )

    page_count = estimate_page_count(script_text)
    job_id = str(uuid.uuid4())
    create_job(job_id)

    logger.info(
        "Coverage requested: file=%s pages≈%d job=%s",
        filename, page_count, job_id,
    )

    # Launch the pipeline in the background
    # Import here to avoid circular imports at module level
    from graph.runner import run_pipeline
    asyncio.create_task(run_pipeline(job_id, script_text, page_count))

    return CoverageJobResponse(job_id=job_id)


# ───────────────────────────────────────────────────────────────────────────
# GET /api/coverage/{job_id}/stream — SSE
# ───────────────────────────────────────────────────────────────────────────

@router.get("/coverage/{job_id}/stream")
async def stream_coverage(job_id: str, request: Request):
    """Server-Sent Events stream of pipeline progress."""

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        while True:
            # Check client disconnect
            if await request.is_disconnected():
                break

            try:
                event = await asyncio.wait_for(job.queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send keepalive
                yield {"event": "keepalive", "data": ""}
                continue

            yield {
                "event": event.get("event", "message"),
                "data": json.dumps(event),
            }

            # Stop streaming after final events
            if event.get("event") in ("complete", "error"):
                break

    return EventSourceResponse(event_generator())


# ───────────────────────────────────────────────────────────────────────────
# GET /api/coverage/{job_id} — fetch result
# ───────────────────────────────────────────────────────────────────────────

@router.get("/coverage/{job_id}", response_model=JobStatusResponse)
async def get_coverage(job_id: str):
    """Retrieve the status and (if complete) the coverage report."""

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ("pending", "running"):
        return JSONResponse(
            status_code=202,
            content={"job_id": job_id, "status": job.status},
        )

    if job.status == "error":
        return JobStatusResponse(
            job_id=job_id,
            status="error",
            error=job.error,
        )

    return JobStatusResponse(
        job_id=job_id,
        status="complete",
        report=job.report,
    )
