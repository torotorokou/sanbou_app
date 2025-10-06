"""
KPI router: dashboard and overview queries.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infra.db import get_db
from app.services.kpi_service import KPIService
from app.domain.models import KPIOverview

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get("/overview", response_model=KPIOverview, summary="Get KPI overview")
def get_overview(
    db: Session = Depends(get_db),
):
    """
    Get aggregated KPIs for the dashboard.
    TODO: Add more detailed breakdowns and filters.
    """
    service = KPIService(db)
    return service.get_overview()
