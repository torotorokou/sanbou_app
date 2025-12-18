"""
PostgreSQLForecastResultRepository: 予測結果の保存（DB実装）
===========================================================
forecast.daily_forecast_results へ予測結果を保存
"""
from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend_shared.application.logging import get_module_logger
from ..ports.forecast_result_repository import (
    ForecastResultRepositoryPort,
    DailyForecastResult
)

logger = get_module_logger(__name__)


class PostgreSQLForecastResultRepository(ForecastResultRepositoryPort):
    """PostgreSQL実装の予測結果リポジトリ"""
    
    def __init__(self, session: Session):
        self._session = session
    
    def save_daily_forecast(
        self,
        result: DailyForecastResult
    ) -> UUID:
        """
        forecast.daily_forecast_results へ予測結果を保存
        
        Args:
            result: 予測結果
        
        Returns:
            UUID: 保存された結果のID
        
        Raises:
            Exception: DB接続エラー、制約違反等
        """
        # input_snapshot を JSON 文字列に変換
        input_snapshot_json = json.dumps(result.input_snapshot or {})
        
        query = text("""
            INSERT INTO forecast.daily_forecast_results (
                target_date,
                job_id,
                p50,
                p10,
                p90,
                unit,
                input_snapshot
            ) VALUES (
                :target_date,
                :job_id,
                :p50,
                :p10,
                :p90,
                :unit,
                :input_snapshot::jsonb
            )
            ON CONFLICT (target_date, job_id) 
            DO UPDATE SET
                p50 = EXCLUDED.p50,
                p10 = EXCLUDED.p10,
                p90 = EXCLUDED.p90,
                unit = EXCLUDED.unit,
                input_snapshot = EXCLUDED.input_snapshot,
                generated_at = CURRENT_TIMESTAMP
            RETURNING id
        """)
        
        logger.debug(
            f"Saving daily forecast: target_date={result.target_date}, "
            f"job_id={result.job_id}, p50={result.p50}"
        )
        
        result_row = self._session.execute(
            query,
            {
                "target_date": result.target_date,
                "job_id": result.job_id,
                "p50": result.p50,
                "p10": result.p10,
                "p90": result.p90,
                "unit": result.unit,
                "input_snapshot": input_snapshot_json,
            }
        )
        
        result_id = result_row.fetchone()[0]
        
        # commit は呼び出し側で行う（トランザクション管理の責務分離）
        
        logger.info(
            f"✅ Saved daily forecast result: "
            f"id={result_id}, target_date={result.target_date}, job_id={result.job_id}"
        )
        
        return UUID(result_id)
