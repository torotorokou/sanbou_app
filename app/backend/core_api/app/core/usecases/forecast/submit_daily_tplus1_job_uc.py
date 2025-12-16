"""
UseCase: SubmitDailyTplus1JobUseCase

日次t+1予測ジョブを手動投入するユースケース
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.core.domain.entities.forecast_job import ForecastJob
from app.core.ports.forecast_job_repository_port_v2 import (
    IForecastJobRepositoryV2,
    DuplicateJobError
)


class SubmitDailyTplus1JobUseCase:
    """
    日次t+1予測ジョブ投入UseCase
    
    機能:
        - 明日（JST）の日次t+1予測ジョブをキューに投入
        - 既に queued/running のジョブがあれば新規作成しない
    
    責務:
        - target_date の算出（明日JST）
        - 重複チェック
        - ジョブの作成
    
    Note:
        - このPhaseでは手動実行のみ（自動実行は次Phase）
        - 実行自体はワーカーが担当
    """
    
    def __init__(self, forecast_job_repo: IForecastJobRepositoryV2):
        self._repo = forecast_job_repo
    
    def execute(self, requested_date: Optional[date] = None) -> ForecastJob:
        """
        日次t+1予測ジョブを投入
        
        Args:
            requested_date: 予測対象日（省略時は明日JST）
        
        Returns:
            ForecastJob: 作成されたジョブ（既存の場合は既存ジョブ）
        
        Raises:
            ValueError: 日付が不正な場合
        """
        # 1. target_date を算出（明日JST）
        if requested_date is None:
            jst = timezone(timedelta(hours=9))
            now_jst = datetime.now(jst)
            target_date = (now_jst + timedelta(days=1)).date()
        else:
            target_date = requested_date
        
        # 2. 既に queued/running のジョブがあるかチェック
        existing_job = self._repo.find_active_job(
            job_type="daily_tplus1",
            target_date=target_date
        )
        if existing_job:
            # 既存ジョブを返す（新規作成しない）
            return existing_job
        
        # 3. 新規ジョブを作成
        job = self._repo.create_job(
            job_type="daily_tplus1",
            target_date=target_date,
            input_snapshot={"requested_date": str(target_date)},
            max_attempt=3
        )
        
        return job
