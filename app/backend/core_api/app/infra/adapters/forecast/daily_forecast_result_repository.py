"""
Daily Forecast Result Repository

日次予測結果の永続化実装。
forecast.daily_forecast_results テーブルへのINSERT/UPDATE/SELECT。
"""
from __future__ import annotations
from datetime import date
from uuid import UUID
import json
from typing import Optional, Dict, Any, TYPE_CHECKING

from sqlalchemy import text

from app.core.ports.daily_forecast_result_repository_port import DailyForecastResultRepositoryPort

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class DailyForecastResultRepository(DailyForecastResultRepositoryPort):
    """日次予測結果リポジトリ"""
    
    def __init__(self, db: "Session"):
        self.db = db
    
    def save_result(
        self,
        target_date: date,
        job_id: UUID,
        p50: float,
        p10: Optional[float],
        p90: Optional[float],
        unit: str,
        input_snapshot: Dict[str, Any]
    ) -> UUID:
        """
        日次予測結果を保存
        
        Args:
            target_date: 予測対象日（t+1）
            job_id: forecast.forecast_jobs.id
            p50: 中央値予測（メイン）
            p10: 10パーセンタイル（下側予測）
            p90: 90パーセンタイル（上側予測）
            unit: 単位（'ton' or 'kg'）
            input_snapshot: 入力データ詳細
        
        Returns:
            保存されたレコードのID
        
        Raises:
            IntegrityError: UNIQUE制約違反
        """
        sql = text("""
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
            RETURNING id
        """)
        
        result = self.db.execute(
            sql,
            {
                "target_date": target_date,
                "job_id": str(job_id),
                "p50": p50,
                "p10": p10,
                "p90": p90,
                "unit": unit,
                "input_snapshot": json.dumps(input_snapshot, ensure_ascii=False)
            }
        )
        
        row = result.fetchone()
        self.db.commit()
        
        return UUID(row[0])
