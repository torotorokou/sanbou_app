"""
Job Poller for Forecast Worker
===============================
Purpose: forecast.forecast_jobs テーブルからジョブをクレームする

機能:
- queued 状態のジョブを SELECT ... FOR UPDATE SKIP LOCKED で取得
- 1件のみクレーム（並行実行時の競合回避）
- ステータスを 'running' に更新
- locked_at, locked_by フィールドを設定
"""
from __future__ import annotations

import os
import socket
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


def get_worker_id() -> str:
    """
    Worker識別子を取得（ホスト名ベース）
    
    Returns:
        str: Worker識別子（例: "forecast_worker@hostname"）
    """
    hostname = socket.gethostname()
    return f"forecast_worker@{hostname}"


def claim_next_job(db: Session) -> Optional[dict]:
    """
    次の実行可能なジョブを1件クレームする
    
    処理フロー:
    1. status='queued' かつ run_after <= NOW のジョブを検索
    2. SELECT ... FOR UPDATE SKIP LOCKED で1件取得（競合回避）
    3. status を 'running' に更新
    4. locked_at, locked_by, started_at をセット
    5. ジョブ情報を返却
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        Optional[dict]: クレームしたジョブ情報（なければNone）
            - id: uuid
            - job_type: str
            - target_date: date
            - input_snapshot: dict
            - attempt: int
            - max_attempt: int
    """
    worker_id = get_worker_id()
    now = datetime.now(timezone.utc)
    
    # SELECT FOR UPDATE SKIP LOCKED でクレーム
    claim_stmt = text("""
        WITH claimed AS (
            SELECT id
            FROM forecast.forecast_jobs
            WHERE status = 'queued'
              AND run_after <= :now
            ORDER BY run_after ASC, created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        UPDATE forecast.forecast_jobs fj
        SET status = 'running',
            locked_at = :now,
            locked_by = :worker_id,
            started_at = :now,
            updated_at = :now
        FROM claimed
        WHERE fj.id = claimed.id
        RETURNING 
            fj.id,
            fj.job_type,
            fj.target_date,
            fj.input_snapshot,
            fj.attempt,
            fj.max_attempt
    """)
    
    try:
        result = db.execute(
            claim_stmt,
            {
                "now": now,
                "worker_id": worker_id
            }
        ).fetchone()
        
        if result is None:
            logger.debug("No jobs available to claim")
            return None
        
        db.commit()
        
        job_info = {
            "id": result[0],
            "job_type": result[1],
            "target_date": result[2],
            "input_snapshot": result[3],
            "attempt": result[4],
            "max_attempt": result[5]
        }
        
        logger.info(
            f"✅ Claimed job: {job_info['job_type']}",
            extra={
                "job_id": str(job_info["id"]),
                "job_type": job_info["job_type"],
                "target_date": str(job_info["target_date"]),
                "attempt": job_info["attempt"],
                "worker_id": worker_id
            }
        )
        
        return job_info
        
    except Exception as e:
        db.rollback()
        logger.error(
            "❌ Failed to claim job",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__}
        )
        return None


def mark_job_succeeded(db: Session, job_id: UUID) -> None:
    """
    ジョブを成功としてマーク
    
    Args:
        db: SQLAlchemy Session
        job_id: ジョブID
    """
    now = datetime.now(timezone.utc)
    
    stmt = text("""
        UPDATE forecast.forecast_jobs
        SET status = 'succeeded',
            finished_at = :now,
            updated_at = :now
        WHERE id = :job_id
    """)
    
    try:
        db.execute(stmt, {"now": now, "job_id": job_id})
        db.commit()
        
        logger.info(
            f"✅ Job marked as succeeded",
            extra={"job_id": str(job_id)}
        )
    except Exception as e:
        db.rollback()
        logger.error(
            "❌ Failed to mark job as succeeded",
            exc_info=True,
            extra={"job_id": str(job_id), "error": str(e)}
        )
        raise


def mark_job_failed(
    db: Session,
    job_id: UUID,
    error_message: str,
    increment_attempt: bool = True
) -> None:
    """
    ジョブを失敗としてマーク
    
    Args:
        db: SQLAlchemy Session
        job_id: ジョブID
        error_message: エラーメッセージ
        increment_attempt: attempt をインクリメントするか
    """
    now = datetime.now(timezone.utc)
    
    if increment_attempt:
        stmt = text("""
            UPDATE forecast.forecast_jobs
            SET status = 'failed',
                last_error = :error_message,
                attempt = attempt + 1,
                finished_at = :now,
                updated_at = :now,
                locked_at = NULL,
                locked_by = NULL
            WHERE id = :job_id
        """)
    else:
        stmt = text("""
            UPDATE forecast.forecast_jobs
            SET status = 'failed',
                last_error = :error_message,
                finished_at = :now,
                updated_at = :now,
                locked_at = NULL,
                locked_by = NULL
            WHERE id = :job_id
        """)
    
    try:
        db.execute(
            stmt,
            {
                "now": now,
                "job_id": job_id,
                "error_message": error_message[:1000]  # エラーメッセージを1000文字に制限
            }
        )
        db.commit()
        
        logger.warning(
            f"⚠️ Job marked as failed",
            extra={
                "job_id": str(job_id),
                "error_message": error_message[:200],
                "increment_attempt": increment_attempt
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(
            "❌ Failed to mark job as failed",
            exc_info=True,
            extra={"job_id": str(job_id), "error": str(e)}
        )
        raise
