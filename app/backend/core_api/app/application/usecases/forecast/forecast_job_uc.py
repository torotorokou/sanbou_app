"""
UseCase: CreateForecastJobUseCase

予測ジョブの作成を担当。

設計方針:
  - Port経由でJobRepositoryにアクセス
  - ビジネスロジックはここに集約
"""
from typing import Optional, List
from datetime import date as date_type

from app.domain.models import ForecastJobCreate, ForecastJobResponse, PredictionDTO
from app.domain.ports.forecast_port import IForecastJobRepository, IForecastQueryRepository


class CreateForecastJobUseCase:
    """予測ジョブ作成UseCase"""
    
    def __init__(self, job_repo: IForecastJobRepository):
        self._job_repo = job_repo
    
    def execute(self, req: ForecastJobCreate) -> ForecastJobResponse:
        """
        予測ジョブを作成してキューに登録
        
        Args:
            req: ジョブ作成リクエスト
            
        Returns:
            ForecastJobResponse: 作成されたジョブ情報
        """
        job_id = self._job_repo.queue_forecast_job(
            job_type=req.job_type,
            target_from=req.target_from,
            target_to=req.target_to,
            actor=req.actor or "system",
            payload_json=req.payload_json,
        )
        
        job = self._job_repo.get_job_by_id(job_id)
        if not job:
            raise RuntimeError(f"Failed to retrieve created job {job_id}")
        
        return ForecastJobResponse.model_validate(job)


class GetForecastJobStatusUseCase:
    """予測ジョブステータス取得UseCase"""
    
    def __init__(self, job_repo: IForecastJobRepository):
        self._job_repo = job_repo
    
    def execute(self, job_id: int) -> Optional[ForecastJobResponse]:
        """
        ジョブIDでステータスを取得
        
        Args:
            job_id: ジョブID
            
        Returns:
            ForecastJobResponse: ジョブ情報、見つからない場合はNone
        """
        job = self._job_repo.get_job_by_id(job_id)
        if not job:
            return None
        
        return ForecastJobResponse.model_validate(job)


class GetPredictionsUseCase:
    """予測結果取得UseCase"""
    
    def __init__(self, query_repo: IForecastQueryRepository):
        self._query_repo = query_repo
    
    def execute(self, from_: date_type, to_: date_type) -> List[PredictionDTO]:
        """
        指定期間の予測結果を取得
        
        Args:
            from_: 開始日
            to_: 終了日
            
        Returns:
            List[PredictionDTO]: 予測結果リスト
        """
        return self._query_repo.list_predictions(from_, to_)
