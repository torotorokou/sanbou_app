"""
Domain Models and DTOs (Pydantic v2) - ドメイン層のデータモデル定義

DEPRECATED: このファイルは機能別ディレクトリへの移行中です。
新しい場所からインポートしてください:
  - Forecast: from app.core.domain.forecast.entities import ForecastJobCreate, PredictionDTO
  - Ingest: from app.core.domain.ingest.entities import ReservationCreate, ReservationResponse
  
このファイルは後方互換性のために残されていますが、将来削除される予定です。

【設計方針】
- Framework Agnostic: フレームワークに依存しない純粋なPydanticモデル
- Immutable: 可能な限り不変（イミュータブル）なデータ構造
- Validation: Pydantic による型検証・バリデーション
- Separation of Concerns: DTO（データ転送）とエンティティ（ビジネスロジック）の分離
"""
import warnings
from datetime import date as date_type, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# ========================================
# Forecast DTOs - Re-export for backward compatibility
# ========================================
warnings.warn(
    "Importing Forecast models from app.core.domain.models is deprecated. "
    "Use app.core.domain.forecast.entities instead.",
    DeprecationWarning,
    stacklevel=2
)

from app.core.domain.forecast.entities import (
    ForecastJobCreate,
    ForecastJobResponse,
    PredictionDTO,
)


# ========================================
# Ingest DTOs - Re-export for backward compatibility
# ========================================
warnings.warn(
    "Importing Ingest models from app.core.domain.models is deprecated. "
    "Use app.core.domain.ingest.entities instead.",
    DeprecationWarning,
    stacklevel=2
)

from app.core.domain.ingest.entities import (
    ReservationCreate,
    ReservationResponse,
)


# ========================================
# KPI DTOs - KPI集計用DTO
# ========================================

class KPIOverview(BaseModel):
    """
    KPI概要DTO（ダッシュボード表示用）
    
    フロントエンドダッシュボードで表示する主要KPIの集計値
    
    Attributes:
        total_jobs: 総ジョブ数
        completed_jobs: 完了ジョブ数
        failed_jobs: 失敗ジョブ数
        latest_prediction_date: 最新の予測日
        last_updated: KPIの最終更新日時
        
    TODO: 
        - 実際の集計クエリによる値の取得
        - キャッシュ機構の実装（パフォーマンス向上）
    """
    total_jobs: int = Field(default=0, description="Total number of forecast jobs")
    completed_jobs: int = Field(default=0, description="Completed jobs")
    failed_jobs: int = Field(default=0, description="Failed jobs")
    latest_prediction_date: Optional[date_type] = Field(default=None, description="Latest prediction date available")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


# ========================================
# External API DTOs - 外部API連携用DTO
# ========================================

class RAGAskRequest(BaseModel):
    """Request to RAG API /ask endpoint."""
    query: str = Field(description="User query for RAG")


class RAGAskResponse(BaseModel):
    """Response from RAG API."""
    answer: str
    sources: Optional[list[str]] = None


class ManualListResponse(BaseModel):
    """Response from Manual API /list endpoint."""
    manuals: list[dict]  # TODO: define proper schema when manual_api contract is clarified


# ========================================
# Dashboard Target DTOs
# ========================================

class TargetMetricsResponse(BaseModel):
    """Response for dashboard target metrics with actuals."""
    ddate: Optional[date_type] = Field(default=None, description="Data date")
    month_target_ton: Optional[float] = Field(default=None, description="Monthly target in tons")
    week_target_ton: Optional[float] = Field(default=None, description="Weekly target in tons")
    day_target_ton: Optional[float] = Field(default=None, description="Daily target in tons")
    month_actual_ton: Optional[float] = Field(default=None, description="Monthly actual in tons")
    week_actual_ton: Optional[float] = Field(default=None, description="Weekly actual in tons")
    day_actual_ton_prev: Optional[float] = Field(default=None, description="Previous day actual in tons")
    iso_year: Optional[int] = Field(default=None, description="ISO year")
    iso_week: Optional[int] = Field(default=None, description="ISO week number")
    iso_dow: Optional[int] = Field(default=None, description="ISO day of week (1=Monday, 7=Sunday)")
    day_type: Optional[str] = Field(default=None, description="Day type (weekday/sat/sun_hol)")
    is_business: Optional[bool] = Field(default=None, description="Is business day")

