"""
KPI UseCase DTOs

Input/Output DTOs for KPI feature following Clean Architecture principles.
"""

from dataclasses import dataclass
from datetime import date as date_type


@dataclass(frozen=True)
class GetKPIOverviewInput:
    """
    Input DTO for getting KPI overview

    Currently no parameters needed (returns global overview),
    but defined for consistency and future extensibility.
    """

    pass


@dataclass(frozen=True)
class GetKPIOverviewOutput:
    """
    Output DTO for KPI overview response

    Attributes:
        total_jobs: 全ジョブ数
        completed_jobs: 完了ジョブ数
        failed_jobs: 失敗ジョブ数
        latest_prediction_date: 最新予測日付
    """

    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    latest_prediction_date: date_type | None
