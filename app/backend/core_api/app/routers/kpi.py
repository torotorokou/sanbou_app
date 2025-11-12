"""
KPI router: dashboard and overview queries.

TODO: UseCase移行待ち
  - 現在はService層を直接呼び出し
  - 将来的に GetKPIOverviewUseCase へ移行予定
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infra.db import get_db
from app.application.usecases.kpi.kpi_service import KPIService
from app.domain.models import KPIOverview

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
