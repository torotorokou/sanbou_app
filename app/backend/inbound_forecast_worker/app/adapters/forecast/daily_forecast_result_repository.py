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

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class DailyForecastResultRepository:
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
            p50: 中央値（50%分位点）= Quantile回帰 alpha=0.5 → median
            p10: 下側区間（median - 1.28σ）= 正規分布仮定、真の10%分位点ではない → lower_1sigma
            p90: 上側90%分位点 = Quantile回帰 alpha=0.9 → upper_quantile_90
            unit: 単位（'ton' or 'kg'）
            input_snapshot: 入力データ詳細
        
        Returns:
            保存されたレコードのID
        
        Raises:
            IntegrityError: UNIQUE制約違反
        
        Note:
            Phase 2: 新カラム（median, lower_1sigma, upper_quantile_90）と
                     旧カラム（p10, p50, p90）の両方に保存（互換性維持）。
                     新カラムは統計的に正確な命名。
                     
        See Also:
            データ契約: docs/development/forecast_interval_data_contract.md
        """
        sql = text("""
            INSERT INTO forecast.daily_forecast_results (
                target_date,
                job_id,
                -- 新カラム（Phase 1で追加、統計的に正確な命名）
                median,
                lower_1sigma,
                upper_quantile_90,
                -- 旧カラム（互換性維持、Phase 3で削除予定）
                p50,
                p10,
                p90,
                unit,
                input_snapshot
            ) VALUES (
                :target_date,
                :job_id,
                -- 新カラムに保存
                :median,
                :lower_1sigma,
                :upper_quantile_90,
                -- 旧カラムにも同じ値を保存（互換性）
                :p50,
                :p10,
                :p90,
                :unit,
                CAST(:input_snapshot AS jsonb)
            )
            RETURNING id
        """)
        
        result = self.db.execute(
            sql,
            {
                "target_date": target_date,
                "job_id": str(job_id),
                # 新カラムに保存
                "median": p50,
                "lower_1sigma": p10,
                "upper_quantile_90": p90,
                # 旧カラムに保存（互換性）
                "p50": p50,
                "p10": p10,
                "p90": p90,
                "unit": unit,
                "input_snapshot": json.dumps(input_snapshot, ensure_ascii=False)
            }
        )
        
        row = result.fetchone()
        self.db.commit()
        
        # row[0] is already UUID type from PostgreSQL
        result_id = row[0]
        if isinstance(result_id, str):
            return UUID(result_id)
        return result_id
