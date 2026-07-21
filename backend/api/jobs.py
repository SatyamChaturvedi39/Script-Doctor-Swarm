"""
In-memory job store for tracking coverage pipeline runs.

Each job has:
  - A status (pending → running → complete | error)
  - An asyncio.Queue for SSE progress events
  - A final CoverageReport (once complete)

For production you'd swap this for Redis or a database;
for a solo dev / demo deployment, in-memory is fine.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from api.schemas import CoverageReport

logger = logging.getLogger("script_doctor.jobs")


@dataclass
class Job:
    job_id: str
    status: str = "pending"  # pending | running | complete | error
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    report: Optional[CoverageReport] = None
    error: Optional[str] = None


# Global job registry  (swap for Redis in prod)
_jobs: dict[str, Job] = {}


def create_job(job_id: str) -> Job:
    """Register a new job."""
    job = Job(job_id=job_id)
    _jobs[job_id] = job
    logger.info("Job created: %s", job_id)
    return job


def get_job(job_id: str) -> Optional[Job]:
    """Retrieve a job by ID."""
    return _jobs.get(job_id)


async def push_event(job_id: str, event: dict) -> None:
    """Push a progress event into the job's queue."""
    job = _jobs.get(job_id)
    if job:
        await job.queue.put(event)


def mark_running(job_id: str) -> None:
    job = _jobs.get(job_id)
    if job:
        job.status = "running"


def mark_complete(job_id: str, report: CoverageReport) -> None:
    job = _jobs.get(job_id)
    if job:
        job.status = "complete"
        job.report = report
        logger.info("Job complete: %s", job_id)


def mark_error(job_id: str, error: str) -> None:
    job = _jobs.get(job_id)
    if job:
        job.status = "error"
        job.error = error
        logger.error("Job error: %s — %s", job_id, error)
