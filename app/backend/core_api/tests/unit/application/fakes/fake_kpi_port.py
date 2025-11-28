"""Fake implementation of KPIQueryPort for unit testing"""
from datetime import date
from typing import Optional

from app.core.ports.kpi_port import KPIQueryPort


class FakeKPIQueryPort(KPIQueryPort):
    """
    Fake implementation for testing KPIUseCase without database dependency.
    
    Allows injecting test data via constructor or setter methods.
    """
    
    def __init__(
        self,
        forecast_job_counts: Optional[dict[str, int]] = None,
        latest_prediction_date: Optional[date] = None,
    ):
        self._forecast_job_counts = forecast_job_counts or {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
        }
        self._latest_prediction_date = latest_prediction_date
    
    def get_forecast_job_counts(self) -> dict[str, int]:
        """Return preset job counts"""
        return self._forecast_job_counts
    
    def get_latest_prediction_date(self) -> Optional[date]:
        """Return preset latest date"""
        return self._latest_prediction_date
    
    # Test helpers
    def set_job_counts(self, counts: dict[str, int]) -> None:
        """Update job counts for testing"""
        self._forecast_job_counts = counts
    
    def set_latest_date(self, latest_date: Optional[date]) -> None:
        """Update latest prediction date for testing"""
        self._latest_prediction_date = latest_date
