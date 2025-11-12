"""
KPI service: aggregations and queries for dashboard.

TODO: 将来的にUseCaseへ移行予定
  - 現在はService層でKPI集計を実施
  - 今後、ダッシュボードフローはUseCaseに移行
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.infra.db.orm_models import ForecastJob, PredictionDaily
from app.domain.models import KPIOverview


class KPIService:
    """Service for KPI and dashboard queries."""

    def __init__(self, db: Session):
        self.db = db

    def get_overview(self) -> KPIOverview:
        """
        Get overview KPIs for the dashboard.
        TODO: Optimize with dedicated aggregation queries.
        """
        total_jobs = self.db.query(func.count(ForecastJob.id)).scalar() or 0
        completed_jobs = (
            self.db.query(func.count(ForecastJob.id)).filter(ForecastJob.status == "done").scalar()
            or 0
        )
        failed_jobs = (
            self.db.query(func.count(ForecastJob.id))
            .filter(ForecastJob.status == "failed")
            .scalar()
            or 0
        )
        latest_prediction_date = (
            self.db.query(func.max(PredictionDaily.date)).scalar()
        )

        return KPIOverview(
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            latest_prediction_date=latest_prediction_date,
            last_updated=datetime.utcnow(),
        )
