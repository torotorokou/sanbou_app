"""
Forecast service: handles job creation, querying, and orchestration.
"""
from typing import Optional
from datetime import date as date_type
from sqlalchemy.orm import Session

from app.repositories.job_repo import JobRepository
from app.repositories.forecast_query_repo import ForecastQueryRepository
from app.domain.models import ForecastJobCreate, ForecastJobResponse, PredictionDTO


class ForecastService:
    """Service for forecast job management."""

    def __init__(self, db: Session):
        self.job_repo = JobRepository(db)
        self.query_repo = ForecastQueryRepository(db)

    def create_forecast_job(self, req: ForecastJobCreate) -> ForecastJobResponse:
        """
        Queue a new forecast job.
        Returns the created job with status='queued'.
        """
        job_id = self.job_repo.queue_forecast_job(
            job_type=req.job_type,
            target_from=req.target_from,
            target_to=req.target_to,
            actor=req.actor or "system",
            payload_json=req.payload_json,
        )
        job = self.job_repo.get_job_by_id(job_id)
        return ForecastJobResponse.model_validate(job)

    def get_job_status(self, job_id: int) -> Optional[ForecastJobResponse]:
        """Retrieve job status by ID."""
        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            return None
        return ForecastJobResponse.model_validate(job)

    def list_predictions(self, from_: date_type, to_: date_type) -> list[PredictionDTO]:
        """Retrieve prediction results within date range."""
        return self.query_repo.list_predictions(from_, to_)
