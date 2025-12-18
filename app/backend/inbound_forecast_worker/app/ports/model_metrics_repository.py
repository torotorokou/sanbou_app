"""
ModelMetricsRepositoryPort: モデル精度指標の保存
===========================================
学習済みモデルの精度指標（MAE/R2等）をDBに保存するためのポート（抽象インターフェース）
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID


@dataclass
class ModelMetrics:
    """モデル精度指標
    
    学習済みモデルのWalk-forward評価等で算出された精度指標を表すドメインモデル。
    """
    job_id: Optional[UUID]  # 予測ジョブID（forecast_jobs.id）
    model_name: str  # 例: 'daily_tplus1'
    model_version: Optional[str]  # 例: 'v20251218' or bundle hash
    
    # 学習期間
    train_window_start: date
    train_window_end: date
    eval_method: str  # 例: 'walkforward'
    
    # 精度指標（コア）
    mae: Decimal  # Mean Absolute Error
    r2: Decimal  # R² score（決定係数）
    n_samples: int  # 評価サンプル数
    
    # 精度指標（追加）
    rmse: Optional[Decimal] = None  # Root Mean Squared Error
    mape: Optional[Decimal] = None  # Mean Absolute Percentage Error
    mae_sum_only: Optional[Decimal] = None  # 品目合計のみのMAE
    r2_sum_only: Optional[Decimal] = None  # 品目合計のみのR²
    
    # メタデータ
    unit: str = "ton"  # 精度指標の単位
    metadata: Optional[Dict] = None  # ハイパーパラメータ等


class ModelMetricsRepositoryPort(ABC):
    """モデル精度指標の保存ポート"""
    
    @abstractmethod
    def save_metrics(
        self,
        metrics: ModelMetrics
    ) -> UUID:
        """
        モデル精度指標をDBに保存
        
        Args:
            metrics: 精度指標
        
        Returns:
            UUID: 保存されたレコードのID
        
        Raises:
            Exception: DB接続エラー、制約違反等
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def list_recent(
        self,
        model_name: str,
        limit: int = 10
    ) -> list[ModelMetrics]:
        """
        最近の精度指標を取得
        
        Args:
            model_name: モデル名（例：'daily_tplus1'）
            limit: 取得件数
        
        Returns:
            精度指標のリスト（created_at降順）
        """
        pass
