"""
KPI API Router
KPI overview and metrics endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
import logging

from app.presentation.schemas import KPIOverview
from app.application.usecases.kpi.kpi_uc import KPIUseCase
from app.config.di_providers import get_kpi_uc

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get("/overview", response_model=KPIOverview, summary="Get KPI overview")
def get_overview(
    uc: KPIUseCase = Depends(get_kpi_uc),
):
    """
    Get aggregated KPIs for the dashboard.
    Follows Clean Architecture with Port&Adapter pattern.
    """
    return uc.get_overview()
