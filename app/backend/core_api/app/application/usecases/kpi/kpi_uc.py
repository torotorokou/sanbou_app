"""
KPI UseCase: aggregations and queries for dashboard.

Port-based implementation following Clean Architecture principles.
"""
from datetime import datetime

from app.domain.ports.kpi_port import KPIQueryPort
from app.domain.models import KPIOverview


class KPIUseCase:
    """UseCase for KPI and dashboard queries."""

    def __init__(self, kpi_query: KPIQueryPort):
        self.kpi_query = kpi_query

    def get_overview(self) -> KPIOverview:
        """
        Get aggregated KPI overview.
        All data comes from Port abstraction (no direct DB access).
        """
        counts = self.kpi_query.get_forecast_job_counts()
        latest_date = self.kpi_query.get_latest_prediction_date()
        
        return KPIOverview(
            total_jobs=sum(counts.values()),
            completed_jobs=counts.get("completed", 0),
            failed_jobs=counts.get("failed", 0),
            latest_prediction_date=latest_date,
        )
