"""
Port: IForecastJobRepository

予測ジョブ管理に必要な抽象インターフェース。
"""

from datetime import date as date_type
from datetime import datetime
from typing import Any, List, Optional, Protocol

from app.core.domain.models import PredictionDTO


class IForecastJobRepository(Protocol):
    """予測ジョブ管理のPort"""

    def queue_forecast_job(
        self,
        *,
        job_type: str,
        target_from: date_type,
        target_to: date_type,
        actor: str = "system",
        payload_json: Optional[dict] = None
    ) -> int:
        """
        予測ジョブをキューに登録

        Returns:
            int: 作成されたジョブID
        """
        ...

    def get_job_by_id(self, job_id: int) -> Optional[Any]:
        """ジョブIDでジョブを取得"""
        ...


class IForecastQueryRepository(Protocol):
    """予測結果取得のPort"""

    def list_predictions(self, from_: date_type, to_: date_type) -> List[PredictionDTO]:
        """予測結果を取得"""
        ...
