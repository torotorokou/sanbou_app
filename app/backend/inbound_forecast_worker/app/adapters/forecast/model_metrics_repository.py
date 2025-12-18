"""
ModelMetrics Repository (PostgreSQL Implementation)

モデル精度指標のDB保存実装。
forecast.model_metrics テーブルへのINSERT/SELECT。
"""
from __future__ import annotations
from datetime import date
from uuid import UUID
import json
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import text

from app.ports.model_metrics_repository import ModelMetrics, ModelMetricsRepositoryPort

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class PostgreSQLModelMetricsRepository(ModelMetricsRepositoryPort):
    """モデル精度指標リポジトリ（PostgreSQL実装）"""
    
    def __init__(self, db: "Session"):
        self.db = db
    
    def save_metrics(
        self,
        metrics: ModelMetrics
    ) -> UUID:
        """
        モデル精度指標を保存
        
        Args:
            metrics: 精度指標
        
        Returns:
            保存されたレコードのID
        
        Raises:
            IntegrityError: 制約違反
        """
        sql = text("""
            INSERT INTO forecast.model_metrics (
                job_id,
                model_name,
                model_version,
                train_window_start,
                train_window_end,
                eval_method,
                mae,
                r2,
                n_samples,
                rmse,
                mape,
                mae_sum_only,
                r2_sum_only,
                unit,
                metadata
            ) VALUES (
                :job_id,
                :model_name,
                :model_version,
                :train_window_start,
                :train_window_end,
                :eval_method,
                :mae,
                :r2,
                :n_samples,
                :rmse,
                :mape,
                :mae_sum_only,
                :r2_sum_only,
                :unit,
                CAST(:metadata AS jsonb)
            )
            RETURNING id
        """)
        
        result = self.db.execute(
            sql,
            {
                "job_id": str(metrics.job_id) if metrics.job_id else None,
                "model_name": metrics.model_name,
                "model_version": metrics.model_version,
                "train_window_start": metrics.train_window_start,
                "train_window_end": metrics.train_window_end,
                "eval_method": metrics.eval_method,
                "mae": float(metrics.mae),
                "r2": float(metrics.r2),
                "n_samples": metrics.n_samples,
                "rmse": float(metrics.rmse) if metrics.rmse is not None else None,
                "mape": float(metrics.mape) if metrics.mape is not None else None,
                "mae_sum_only": float(metrics.mae_sum_only) if metrics.mae_sum_only is not None else None,
                "r2_sum_only": float(metrics.r2_sum_only) if metrics.r2_sum_only is not None else None,
                "unit": metrics.unit,
                "metadata": json.dumps(metrics.metadata or {}, ensure_ascii=False)
            }
        )
        
        row = result.fetchone()
        if row is None:
            raise RuntimeError("Failed to insert model_metrics: no row returned")
        
        self.db.commit()
        
        # row[0] is already UUID type from PostgreSQL
        metrics_id = row[0]
        if isinstance(metrics_id, str):
            return UUID(metrics_id)
        return metrics_id
    
    def get_by_job_id(
        self,
        job_id: UUID
    ) -> Optional[ModelMetrics]:
        """
        ジョブIDから精度指標を取得
        
        Args:
            job_id: 予測ジョブID
        
        Returns:
            精度指標（存在しない場合はNone）
        """
        sql = text("""
            SELECT
                job_id,
                model_name,
                model_version,
                train_window_start,
                train_window_end,
                eval_method,
                mae,
                r2,
                n_samples,
                rmse,
                mape,
                mae_sum_only,
                r2_sum_only,
                unit,
                metadata
            FROM forecast.model_metrics
            WHERE job_id = :job_id
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        result = self.db.execute(sql, {"job_id": str(job_id)})
        row = result.fetchone()
        
        if row is None:
            return None
        
        return ModelMetrics(
            job_id=UUID(row.job_id) if row.job_id else None,
            model_name=row.model_name,
            model_version=row.model_version,
            train_window_start=row.train_window_start,
            train_window_end=row.train_window_end,
            eval_method=row.eval_method,
            mae=row.mae,
            r2=row.r2,
            n_samples=row.n_samples,
            rmse=row.rmse,
            mape=row.mape,
            mae_sum_only=row.mae_sum_only,
            r2_sum_only=row.r2_sum_only,
            unit=row.unit,
            metadata=row.metadata
        )
    
    def list_recent(
        self,
        model_name: str,
        limit: int = 10
    ) -> List[ModelMetrics]:
        """
        最近の精度指標を取得
        
        Args:
            model_name: モデル名（例：'daily_tplus1'）
            limit: 取得件数
        
        Returns:
            精度指標のリスト（created_at降順）
        """
        sql = text("""
            SELECT
                job_id,
                model_name,
                model_version,
                train_window_start,
                train_window_end,
                eval_method,
                mae,
                r2,
                n_samples,
                rmse,
                mape,
                mae_sum_only,
                r2_sum_only,
                unit,
                metadata
            FROM forecast.model_metrics
            WHERE model_name = :model_name
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(sql, {"model_name": model_name, "limit": limit})
        rows = result.fetchall()
        
        return [
            ModelMetrics(
                job_id=UUID(row.job_id) if row.job_id else None,
                model_name=row.model_name,
                model_version=row.model_version,
                train_window_start=row.train_window_start,
                train_window_end=row.train_window_end,
                eval_method=row.eval_method,
                mae=row.mae,
                r2=row.r2,
                n_samples=row.n_samples,
                rmse=row.rmse,
                mape=row.mape,
                mae_sum_only=row.mae_sum_only,
                r2_sum_only=row.r2_sum_only,
                unit=row.unit,
                metadata=row.metadata
            )
            for row in rows
        ]
