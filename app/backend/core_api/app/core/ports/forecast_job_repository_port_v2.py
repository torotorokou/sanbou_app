"""
Port: IForecastJobRepositoryV2

forecast.forecast_jobs テーブル用のリポジトリPort
日次/週次/月次予測ジョブの管理を担当
"""
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from app.core.domain.entities.forecast_job import ForecastJob


class IForecastJobRepositoryV2(ABC):
    """
    予測ジョブリポジトリのPort（V2: forecast.forecast_jobs テーブル用）
    
    責務:
        - ジョブの作成（queued）
        - ジョブの取得
        - 重複チェック（既に queued/running のジョブがあるか）
    
    Note:
        - ジョブのクレーム/更新はワーカー側で実装
        - このPortはAPI側で使用
    """
    
    @abstractmethod
    def create_job(
        self,
        *,
        job_type: str,
        target_date: date,
        run_after: Optional[datetime] = None,
        input_snapshot: Optional[dict] = None,
        max_attempt: int = 3
    ) -> ForecastJob:
        """
        新規ジョブを作成（status='queued'）
        
        Args:
            job_type: ジョブタイプ（'daily_tplus1'等）
            target_date: 予測対象日
            run_after: 実行可能時刻（省略時は即時実行可能）
            input_snapshot: 入力パラメータのスナップショット
            max_attempt: 最大試行回数
        
        Returns:
            ForecastJob: 作成されたジョブ
        
        Raises:
            DuplicateJobError: 既に同一(job_type, target_date)のジョブが queued/running 状態で存在する場合
        """
        ...
    
    @abstractmethod
    def get_job_by_id(self, job_id: UUID) -> Optional[ForecastJob]:
        """
        ジョブIDでジョブを取得
        
        Args:
            job_id: ジョブID（UUID）
        
        Returns:
            ForecastJob | None: 見つかった場合はジョブ、見つからない場合はNone
        """
        ...
    
    @abstractmethod
    def find_active_job(
        self,
        *,
        job_type: str,
        target_date: date
    ) -> Optional[ForecastJob]:
        """
        アクティブなジョブを検索（queued または running）
        
        Args:
            job_type: ジョブタイプ
            target_date: 予測対象日
        
        Returns:
            ForecastJob | None: 見つかった場合はジョブ、見つからない場合はNone
        """
        ...


class DuplicateJobError(Exception):
    """重複ジョブエラー"""
    pass
