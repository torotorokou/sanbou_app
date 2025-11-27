"""Forecast adapters"""

from app.infra.adapters.forecast.job_repository import JobRepository
from app.infra.adapters.forecast.forecast_query_repository import ForecastQueryRepository

__all__ = ["JobRepository", "ForecastQueryRepository"]
