"""
Job Repository - 予測ジョブ管理リポジトリ

jobs.forecast_jobsテーブルに対する操作を担当。
主な機能:
  - ジョブのキュー登録(非同期実行用)
  - ジョブのクレーム(FOR UPDATE SKIP LOCKEDで排他制御)
  - ステータス更新(done/failed)
  - ジョブ情報の取得

設計上のポイント:
  - ワーカープロセス(forecast_worker)が複数同時実行されても安全
  - FOR UPDATE SKIP LOCKEDを使用して、同一ジョブの重複実行を防止
  - attemptsカウンタでリトライ回数を管理
"""
from typing import Optional
from datetime import date as date_type, datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infra.db.orm_models import ForecastJob


class JobRepository:
    """Repository for forecast job management."""

    def __init__(self, db: Session):
        self.db = db

    def queue_forecast_job(
        self,
        job_type: str,
        target_from: date_type,
        target_to: date_type,
        actor: str = "system",
        payload_json: Optional[dict] = None,
        scheduled_for: Optional[datetime] = None,
    ) -> int:
        """
        新しい予測ジョブをキューに登録
        
        ジョブはstatus='queued'で作成され、ワーカープロセスによって
        非同期に実行されます。
        
        Args:
            job_type: ジョブタイプ(例: 'daily', 'weekly')
            target_from: 予測対象期間の開始日
            target_to: 予測対象期間の終了日
            actor: ジョブを登録したユーザーまたはシステム(デフォルト: 'system')
            payload_json: 追加パラメータ(JSON形式)
            scheduled_for: 実行予定時刻(省略時は即座に実行可能)
            
        Returns:
            int: 作成されたジョブのID
            
        Raises:
            SQLAlchemyError: データベースエラー
        """
        job = ForecastJob(
            job_type=job_type,
            target_from=target_from,
            target_to=target_to,
            status="queued",  # 初期状態: 待機中
            attempts=0,        # 実行回数: 0
            actor=actor,
            payload_json=payload_json,
            scheduled_for=scheduled_for,
        )
        self.db.add(job)
        self.db.flush()  # IDを取得するためflush(トランザクションはまだコミットしない)
        return job.id

    def claim_one_queued_job_for_update(self) -> Optional[int]:
        """
        待機中のジョブを1つクレームし、実行中状態に変更
        
        FOR UPDATE SKIP LOCKEDを使用して、複数のワーカープロセスが
        同時に実行されても、同一ジョブが重複して実行されることを防止。
        
        処理フロー:
          1. status='queued' かつ scheduled_for <= NOW() のジョブを検索
          2. FOR UPDATE SKIP LOCKED でロック取得(他プロセスがロック中ならスキップ)
          3. status='running' に変更、attempts を +1
          4. トランザクションコミット
        
        Returns:
            Optional[int]: クレームしたジョブのID、または利用可能なジョブがない場合はNone
            
        Note:
            このメソッドは自動的にcommitするため、呼び出し側でのコミットは不要。
        """
        sql = text("""
            WITH picked AS (
                SELECT id FROM jobs.forecast_jobs
                WHERE status = 'queued'
                  AND (scheduled_for IS NULL OR scheduled_for <= NOW())
                ORDER BY id
                FOR UPDATE SKIP LOCKED  -- ロック取得済みの行はスキップ(他ワーカーとの競合回避)
                LIMIT 1
            )
            UPDATE jobs.forecast_jobs
            SET status = 'running',          -- 実行中に変更
                attempts = attempts + 1,     -- 実行回数をインクリメント
                updated_at = NOW()           -- 更新時刻を記録
            WHERE id IN (SELECT id FROM picked)
            RETURNING id
        """)
        result = self.db.execute(sql).fetchone()
        self.db.commit()  # トランザクションを即座にコミット(他ワーカーに可視化)
        return result[0] if result else None

    def mark_done(self, job_id: int) -> None:
        """Mark job as done."""
        job = self.db.query(ForecastJob).filter(ForecastJob.id == job_id).first()
        if job:
            job.status = "done"
            job.updated_at = datetime.utcnow()
            self.db.commit()

    def mark_failed(self, job_id: int, error_message: str) -> None:
        """Mark job as failed with error message."""
        job = self.db.query(ForecastJob).filter(ForecastJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = error_message
            job.updated_at = datetime.utcnow()
            self.db.commit()

    def get_job_by_id(self, job_id: int) -> Optional[ForecastJob]:
        """Retrieve job by ID."""
        return self.db.query(ForecastJob).filter(ForecastJob.id == job_id).first()
