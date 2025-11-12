"""
Forecast router: job creation, status, and prediction results.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date as date_type

from app.config.di_providers import (
    get_create_forecast_job_uc,
    get_forecast_job_status_uc,
    get_predictions_uc,
)
from app.application.usecases.forecast.forecast_job_uc import (
    CreateForecastJobUseCase,
    GetForecastJobStatusUseCase,
    GetPredictionsUseCase,
)
from app.presentation.schemas import ForecastJobCreate, ForecastJobResponse, PredictionDTO

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.post("/jobs", response_model=ForecastJobResponse, summary="Create forecast job")
def create_forecast_job(
    req: ForecastJobCreate,
    uc: CreateForecastJobUseCase = Depends(get_create_forecast_job_uc),
):
    """
    Queue a new forecast job.
    The job will be picked up by forecast_worker and executed asynchronously.
    """
    return uc.execute(req)


@router.get("/jobs/{job_id}", response_model=ForecastJobResponse, summary="Get job status")
def get_job_status(
    job_id: int,
    uc: GetForecastJobStatusUseCase = Depends(get_forecast_job_status_uc),
):
    """
    Retrieve the status and metadata of a forecast job.
    """
    job = uc.execute(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/predictions", response_model=list[PredictionDTO], summary="Get predictions")
def get_predictions(
    from_date: date_type = Query(..., alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: date_type = Query(..., alias="to", description="End date (YYYY-MM-DD)"),
    uc: GetPredictionsUseCase = Depends(get_predictions_uc),
):
    """
    Retrieve forecast predictions within the specified date range.
    """
    return uc.execute(from_=from_date, to_=to_date)
