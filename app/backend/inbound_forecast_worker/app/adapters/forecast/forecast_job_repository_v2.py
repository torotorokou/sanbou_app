# -*- coding: utf-8 -*-
"""
Adapter: PostgresForecastJobRepositoryV2

forecast.forecast_jobs テーブル用のリポジトリ実装
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import text, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend_shared.application.logging import get_module_logger
from app.core.domain.entities.forecast_job import ForecastJob
from app.core.ports.forecast_job_repository_port_v2 import (
    IForecastJobRepositoryV2,
    DuplicateJobError
)


logger = get_module_logger(__name__)


class PostgresForecastJobRepositoryV2(IForecastJobRepositoryV2):
    """
    PostgreSQL implementation of IForecastJobRepositoryV2
    
    Note:
        - forecast.forecast_jobs テーブルを直接操作
        - ORMモデルは作成せず、text() + dict で実装（軽量）
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_job(
        self,
        *,
        job_type: str,
        target_date,
        run_after: Optional[datetime] = None,
        input_snapshot: Optional[dict] = None,
        max_attempt: int = 3
    ) -> ForecastJob:
        """
        新規ジョブを作成（status='queued'）
        
        Raises:
            DuplicateJobError: ユニーク制約違反（既に queued/running のジョブが存在）
        """
        try:
            if run_after is None:
                run_after = datetime.now(timezone.utc)
            
            if input_snapshot is None:
                input_snapshot = {}
            
            # JSONBパラメータはJSON文字列に変換
            import json
            input_snapshot_json = json.dumps(input_snapshot)
            
            stmt = text("""
                INSERT INTO forecast.forecast_jobs (
                    job_type, target_date, status, run_after, 
                    input_snapshot, max_attempt
                )
                VALUES (
                    :job_type, :target_date, 'queued', :run_after,
                    CAST(:input_snapshot AS jsonb), :max_attempt
                )
                RETURNING 
                    id, job_type, target_date, status, run_after,
                    locked_at, locked_by, attempt, max_attempt,
                    input_snapshot, last_error, created_at, updated_at,
                    started_at, finished_at
            """)
            
            result = self.db.execute(stmt, {
                "job_type": job_type,
                "target_date": target_date,
                "run_after": run_after,
                "input_snapshot": input_snapshot_json,
                "max_attempt": max_attempt
            }).fetchone()
            
            self.db.commit()
            
            return self._row_to_entity(result)
            
        except IntegrityError as e:
            self.db.rollback()
            if "idx_forecast_jobs_unique_active" in str(e):
                raise DuplicateJobError(
                    f"Job already exists: job_type={job_type}, target_date={target_date}"
                ) from e
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create forecast job: {e}", exc_info=True)
            raise
    
    def get_job_by_id(self, job_id: UUID) -> Optional[ForecastJob]:
        """ジョブIDでジョブを取得"""
        try:
            stmt = text("""
                SELECT 
                    id, job_type, target_date, status, run_after,
                    locked_at, locked_by, attempt, max_attempt,
                    input_snapshot, last_error, created_at, updated_at,
                    started_at, finished_at
                FROM forecast.forecast_jobs
                WHERE id = :job_id
            """)
            
            result = self.db.execute(stmt, {"job_id": str(job_id)}).fetchone()
            
            if result is None:
                return None
            
            return self._row_to_entity(result)
            
        except Exception as e:
            logger.error(f"Failed to get forecast job: {e}", exc_info=True)
            raise
    
    def find_active_job(
        self,
        *,
        job_type: str,
        target_date
    ) -> Optional[ForecastJob]:
        """アクティブなジョブを検索（queued または running）"""
        try:
            stmt = text("""
                SELECT 
                    id, job_type, target_date, status, run_after,
                    locked_at, locked_by, attempt, max_attempt,
                    input_snapshot, last_error, created_at, updated_at,
                    started_at, finished_at
                FROM forecast.forecast_jobs
                WHERE job_type = :job_type
                  AND target_date = :target_date
                  AND status IN ('queued', 'running')
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            result = self.db.execute(stmt, {
                "job_type": job_type,
                "target_date": target_date
            }).fetchone()
            
            if result is None:
                return None
            
            return self._row_to_entity(result)
            
        except Exception as e:
            logger.error(f"Failed to find active forecast job: {e}", exc_info=True)
            raise
    
    def _row_to_entity(self, row) -> ForecastJob:
        """データベース行をドメインエンティティに変換"""
        return ForecastJob(
            id=row.id if isinstance(row.id, UUID) else UUID(row.id),
            job_type=row.job_type,
            target_date=row.target_date,
            status=row.status,
            run_after=row.run_after,
            locked_at=row.locked_at,
            locked_by=row.locked_by,
            attempt=row.attempt,
            max_attempt=row.max_attempt,
            input_snapshot=row.input_snapshot,
            last_error=row.last_error,
            created_at=row.created_at,
            updated_at=row.updated_at,
            started_at=row.started_at,
            finished_at=row.finished_at
        )
