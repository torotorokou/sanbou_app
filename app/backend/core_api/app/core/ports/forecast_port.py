"""
Port: IForecastJobRepository

予測ジョブ管理に必要な抽象インターフェース。
"""
from typing import Protocol, Optional, List, Any
from datetime import date as date_type, datetime

from app.core.domain.forecast.entities import PredictionDTO


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
    
    def mark_running(self, job_id: int) -> None:
        """ジョブをRUNNING状態に更新"""
        ...
    
    def mark_done(self, job_id: int) -> None:
        """ジョブをDONE状態に更新"""
        ...
    
    def mark_failed(self, job_id: int, error_message: str) -> None:
        """ジョブをFAILED状態に更新"""
        ...


class IForecastQueryRepository(Protocol):
    """予測結果取得のPort"""
    
    def list_predictions(self, from_: date_type, to_: date_type) -> List[PredictionDTO]:
        """予測結果を取得"""
        ...
