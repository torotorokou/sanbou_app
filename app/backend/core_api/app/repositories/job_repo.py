"""
Job repository: operations on jobs.forecast_jobs table.
Handles job queuing, claiming (FOR UPDATE SKIP LOCKED), status updates.
"""
from typing import Optional
from datetime import date as date_type, datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.repositories.orm_models import ForecastJob


class JobRepository:
    """Repository for forecast job management."""

    def __init__(self, db: Session):
        self.db = db

    def queue_forecast_job(
        self,
        job_type: str,
        target_from: date_type,
        target_to: date_type,
        actor: str = "system",
        payload_json: Optional[dict] = None,
        scheduled_for: Optional[datetime] = None,
    ) -> int:
        """
        Create a new forecast job with status='queued'.
        Returns the job ID.
        """
        job = ForecastJob(
            job_type=job_type,
            target_from=target_from,
            target_to=target_to,
            status="queued",
            attempts=0,
            actor=actor,
            payload_json=payload_json,
            scheduled_for=scheduled_for,
        )
        self.db.add(job)
        self.db.flush()
        return job.id

    def claim_one_queued_job_for_update(self) -> Optional[int]:
        """
        Claim one queued job using FOR UPDATE SKIP LOCKED.
        Atomically sets status='running' and increments attempts.
        Returns job ID if claimed, else None.
        """
        sql = text("""
            WITH picked AS (
                SELECT id FROM jobs.forecast_jobs
                WHERE status = 'queued'
                  AND (scheduled_for IS NULL OR scheduled_for <= NOW())
                ORDER BY id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE jobs.forecast_jobs
            SET status = 'running', attempts = attempts + 1, updated_at = NOW()
            WHERE id IN (SELECT id FROM picked)
            RETURNING id
        """)
        result = self.db.execute(sql).fetchone()
        self.db.commit()
        return result[0] if result else None

    def mark_done(self, job_id: int) -> None:
        """Mark job as done."""
        job = self.db.query(ForecastJob).filter(ForecastJob.id == job_id).first()
        if job:
            job.status = "done"
            job.updated_at = datetime.utcnow()
            self.db.commit()

    def mark_failed(self, job_id: int, error_message: str) -> None:
        """Mark job as failed with error message."""
        job = self.db.query(ForecastJob).filter(ForecastJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = error_message
            job.updated_at = datetime.utcnow()
            self.db.commit()

    def get_job_by_id(self, job_id: int) -> Optional[ForecastJob]:
        """Retrieve job by ID."""
        return self.db.query(ForecastJob).filter(ForecastJob.id == job_id).first()
