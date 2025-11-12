"""
KPI API Router
KPI overview and metrics endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.domain.models import KPIOverview
from app.application.usecases.kpi.kpi_service import KPIService
from app.deps import get_db

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get("/overview", response_model=KPIOverview, summary="Get KPI overview")
def get_overview(
    db: Session = Depends(get_db),
):
    """
    Get aggregated KPIs for the dashboard.
    TODO: Add more detailed breakdowns and filters.
    TODO: Migrate to UseCase pattern (GetKPIOverviewUseCase)
    """
    service = KPIService(db)
    return service.get_overview()
