"""
KPI Query Adapter

KPIQueryPortの実装。PostgreSQL/SQLAlchemyを使用してKPI集計データを取得。
"""

from datetime import date as date_type

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infra.db.orm_models import ForecastJob, PredictionDaily


class KPIQueryAdapter:
    """KPI集計データ取得のAdapter（KPIQueryPort実装）"""

    def __init__(self, db: Session):
        self.db = db

    def get_forecast_job_counts(self) -> dict[str, int]:
        """
        予測ジョブの件数をステータス別に集計

        ダッシュボードにKPIとして表示するための集計データ。

        Returns:
            dict[str, int]: {
                "total": 全ジョブ数(全ステータス含む),
                "completed": 完了ジョブ数(status='done'),
                "failed": 失敗ジョブ数(status='failed')
            }

        Note:
            - totalはcompleted + failed + queued + running の合計
            - データベースにジョブがない場合はすべて0
        """
        # 全ジョブ数をカウント
        total = self.db.query(func.count(ForecastJob.id)).scalar() or 0

        # 完了ジョブ数をカウント(status='done')
        completed = (
            self.db.query(func.count(ForecastJob.id))
            .filter(ForecastJob.status == "done")
            .scalar()
            or 0
        )

        # 失敗ジョブ数をカウント(status='failed')
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

    def get_latest_prediction_date(self) -> date_type | None:
        """
        最新の予測結果の日付を取得

        forecast.predictions_dailyテーブルの中で最も未来の日付を返す。
        ダッシュボードで「最終予測日」を表示するために使用。

        Returns:
            Optional[date_type]: 最新の予測日付、または予測データがない場合はNone

        Note:
            - 予測データが存在しない場合、Noneが返される
            - ダッシュボードでは "--" などの代替表示をすることを推奨
        """
        return self.db.query(func.max(PredictionDaily.date)).scalar()
