"""
KPI Query Port

KPI集計データ取得のためのPort（抽象インターフェース）
"""

from datetime import date as date_type
from typing import Protocol


class KPIQueryPort(Protocol):
    """KPI集計データ取得のPort"""

    def get_forecast_job_counts(self) -> dict[str, int]:
        """
        予測ジョブの件数を取得

        Returns:
            dict: {
                "total": 全件数,
                "completed": 完了件数,
                "failed": 失敗件数
            }
        """
        ...

    def get_latest_prediction_date(self) -> date_type | None:
        """
        最新の予測日付を取得

        Returns:
            date | None: 最新の予測日付（データがない場合はNone）
        """
        ...
