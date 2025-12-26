"""
Forecast Query Repository - 予測結果取得リポジトリ

forecast.predictions_dailyテーブルに対する読み取り専用操作。
機能:
  - 指定期間の予測結果を取得
  - 予測値(y_hat)、信頼区間(y_lo, y_hi)、モデルバージョンを含む

設計上のポイント:
  - 読み取り専用のため更新操作は行わない(CQRSパターン)
  - ドメインモデル(PredictionDTO)に変換して返却
"""

from datetime import date as date_type

from sqlalchemy.orm import Session

from app.core.domain.models import PredictionDTO
from app.infra.db.orm_models import PredictionDaily


class ForecastQueryRepository:
    """Repository for reading forecast predictions."""

    def __init__(self, db: Session):
        self.db = db

    def list_predictions(self, from_: date_type, to_: date_type) -> list[PredictionDTO]:
        """
        指定期間内の予測結果を取得

        期間[from_, to_]（両端含む）内の予測結果を日付順に取得し、
        ドメインモデル(PredictionDTO)のリストとして返却。

        Args:
            from_: 開始日(含む)
            to_: 終了日(含む)

        Returns:
            List[PredictionDTO]: 予測結果のリスト(日付昇順)

        Note:
            - y_lo, y_hi はNULLの場合あり(信頼区間が計算されていない場合)
            - model_version は使用された予測モデルのバージョンを記録
        """
        rows = (
            self.db.query(PredictionDaily)
            .filter(PredictionDaily.date >= from_, PredictionDaily.date <= to_)
            .order_by(PredictionDaily.date)  # 日付昇順でソート
            .all()
        )
        # ORMモデルをドメインモデル(DTO)に変換
        return [
            PredictionDTO(
                date=row.date,
                y_hat=float(row.y_hat),  # 予測値
                y_lo=float(row.y_lo) if row.y_lo else None,  # 信頼区間下限
                y_hi=float(row.y_hi) if row.y_hi else None,  # 信頼区間上限
                model_version=row.model_version,  # モデルバージョン
                generated_at=row.generated_at,  # 予測生成日時
            )
            for row in rows
        ]
