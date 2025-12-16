"""
Domain Entity: ForecastJob

forecast.forecast_jobs テーブルに対応するドメインモデル
日次/週次/月次予測ジョブを表現
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ForecastJobId:
    """ForecastJob の識別子（Value Object）"""
    value: UUID


@dataclass
class ForecastJob:
    """
    予測ジョブのドメインエンティティ
    
    Attributes:
        id: ジョブID（UUID）
        job_type: ジョブタイプ（'daily_tplus1', 'weekly'等）
        target_date: 予測対象日
        status: ジョブステータス（'queued', 'running', 'succeeded', 'failed'）
        run_after: 実行可能時刻
        locked_at: ロック時刻（ワーカーがクレームした時刻）
        locked_by: ワーカーID
        attempt: 試行回数
        max_attempt: 最大試行回数
        input_snapshot: 入力パラメータのスナップショット
        last_error: 最後のエラーメッセージ
        created_at: 作成日時
        updated_at: 更新日時
        started_at: 実行開始日時
        finished_at: 実行終了日時
    """
    id: UUID
    job_type: str
    target_date: date
    status: str
    run_after: datetime
    locked_at: Optional[datetime]
    locked_by: Optional[str]
    attempt: int
    max_attempt: int
    input_snapshot: dict
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    
    def is_queued(self) -> bool:
        """キュー待ち状態か"""
        return self.status == "queued"
    
    def is_running(self) -> bool:
        """実行中か"""
        return self.status == "running"
    
    def is_succeeded(self) -> bool:
        """成功したか"""
        return self.status == "succeeded"
    
    def is_failed(self) -> bool:
        """失敗したか"""
        return self.status == "failed"
    
    def is_terminal(self) -> bool:
        """終了状態か（成功または失敗）"""
        return self.is_succeeded() or self.is_failed()
    
    def can_retry(self) -> bool:
        """リトライ可能か"""
        return self.attempt < self.max_attempt
