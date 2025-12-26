"""Fake implementation of KPIQueryPort for unit testing"""

from datetime import date

from app.core.ports.kpi_port import KPIQueryPort


class FakeKPIQueryPort(KPIQueryPort):
    """
    Fake implementation for testing KPIUseCase without database dependency.

    Allows injecting test data via constructor or setter methods.
    """

    def __init__(
        self,
        forecast_job_counts: dict[str, int] | None = None,
        latest_prediction_date: date | None = None,
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

    def get_latest_prediction_date(self) -> date | None:
        """Return preset latest date"""
        return self._latest_prediction_date

    # Test helpers
    def set_job_counts(self, counts: dict[str, int]) -> None:
        """Update job counts for testing"""
        self._forecast_job_counts = counts

    def set_latest_date(self, latest_date: date | None) -> None:
        """Update latest prediction date for testing"""
        self._latest_prediction_date = latest_date
