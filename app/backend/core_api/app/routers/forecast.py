"""
Forecast router: job creation, status, and prediction results.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date as date_type

from app.infra.db import get_db
from app.services.forecast_service import ForecastService
from app.domain.models import ForecastJobCreate, ForecastJobResponse, PredictionDTO

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.post("/jobs", response_model=ForecastJobResponse, summary="Create forecast job")
def create_forecast_job(
    req: ForecastJobCreate,
    db: Session = Depends(get_db),
):
    """
    Queue a new forecast job.
    The job will be picked up by forecast_worker and executed asynchronously.
    """
    service = ForecastService(db)
    return service.create_forecast_job(req)


@router.get("/jobs/{job_id}", response_model=ForecastJobResponse, summary="Get job status")
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve the status and metadata of a forecast job.
    """
    service = ForecastService(db)
    job = service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/predictions", response_model=list[PredictionDTO], summary="Get predictions")
def get_predictions(
    from_date: date_type = Query(..., alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: date_type = Query(..., alias="to", description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Retrieve forecast predictions within the specified date range.
    """
    service = ForecastService(db)
    return service.list_predictions(from_=from_date, to_=to_date)
