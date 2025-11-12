"""
KPI Query Adapter

KPIQueryPortの実装。PostgreSQL/SQLAlchemyを使用してKPI集計データを取得。
"""
from typing import Optional
from datetime import date as date_type
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.infra.db.orm_models import ForecastJob, PredictionDaily


class KPIQueryAdapter:
    """KPI集計データ取得のAdapter（KPIQueryPort実装）"""

    def __init__(self, db: Session):
        self.db = db

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
        total = self.db.query(func.count(ForecastJob.id)).scalar() or 0
        completed = (
            self.db.query(func.count(ForecastJob.id))
            .filter(ForecastJob.status == "done")
            .scalar()
            or 0
        )
        failed = (
            self.db.query(func.count(ForecastJob.id))
            .filter(ForecastJob.status == "failed")
            .scalar()
            or 0
        )

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
        }

    def get_latest_prediction_date(self) -> Optional[date_type]:
        """
        最新の予測日付を取得
        
        Returns:
            date | None: 最新の予測日付（データがない場合はNone）
        """
        return self.db.query(func.max(PredictionDaily.date)).scalar()
