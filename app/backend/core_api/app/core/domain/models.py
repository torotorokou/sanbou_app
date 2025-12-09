"""
Domain Models and DTOs (Pydantic v2) - ドメイン層のデータモデル定義

【概要】
Clean Architecture のドメイン層で使用するデータ転送オブジェクト(DTO)を定義します。
フレームワーク非依存（FastAPI依存なし）な純粋なドメインモデルです。

【設計方針】
- Framework Agnostic: フレームワークに依存しない純粋なPydanticモデル
- Immutable: 可能な限り不変（イミュータブル）なデータ構造
- Validation: Pydantic による型検証・バリデーション
- Separation of Concerns: DTO（データ転送）とエンティティ（ビジネスロジック）の分離

【将来計画】
現在は主にDTO（Data Transfer Object）を定義していますが、
Clean Architecture の完全な実装に向けて以下のリファクタリングを予定:

1. エンティティの分離
   - 現在: このファイルで混在
   - 将来: domain/entities/ ディレクトリへ移動
   - ビジネスロジックを持つリッチなドメインエンティティ

2. 値オブジェクトの分離
   - 現在: 一部のクラスは実質的に値オブジェクト
   - 将来: domain/value_objects/ ディレクトリへ移動
   - 不変性とビジネスルールを持つ値オブジェクト

3. ビジネスロジックの記述
   - 外部依存ゼロでビジネスルールを記述
   - ドメインサービス、集約ルートの実装
   - ユースケース層からの呼び出し

【使用例】
```python
from app.core.domain.models import ForecastJobCreate, PredictionDTO

# ジョブ作成リクエスト
job_req = ForecastJobCreate(
    job_type="daily",
    target_from=date(2025, 1, 1),
    target_to=date(2025, 1, 31),
    actor="user@example.com"
)

# 予測結果
prediction = PredictionDTO(
    date=date(2025, 1, 1),
    y_hat=1500.0,
    y_lo=1200.0,
    y_hi=1800.0,
    model_version="v1.2.3"
)
```
"""
from datetime import date as date_type, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ========================================
# Job DTOs - ジョブ管理用DTO
# ========================================

class ForecastJobCreate(BaseModel):
    """
    予測ジョブ作成リクエスト
    
    Attributes:
        job_type: ジョブタイプ（例: "daily", "weekly", "monthly"）
        target_from: 予測期間の開始日
        target_to: 予測期間の終了日
        actor: ジョブを実行するアクター（ユーザーIDまたは"system"）
        payload_json: 追加のジョブパラメータ（JSONオブジェクト）
    """
    job_type: str = Field(default="daily", description="Type of forecast job")
    target_from: date_type = Field(description="Start date of forecast range")
    target_to: date_type = Field(description="End date of forecast range")
    actor: Optional[str] = Field(default="system", description="User or system actor")
    payload_json: Optional[dict] = Field(default=None, description="Additional job parameters")


class ForecastJobResponse(BaseModel):
    """
    予測ジョブレスポンス
    
    ジョブ作成後またはステータス確認時に返却されるデータ
    
    Attributes:
        id: ジョブID（DB自動採番）
        job_type: ジョブタイプ
        target_from: 予測期間の開始日
        target_to: 予測期間の終了日
        status: ジョブステータス（queued | running | done | failed）
        attempts: 実行試行回数（リトライ回数）
        scheduled_for: ジョブの実行予定時刻（NULL=即時実行）
        actor: ジョブを実行したアクター
        payload_json: ジョブパラメータ
        error_message: エラーメッセージ（失敗時のみ）
        created_at: ジョブ作成日時
        updated_at: ジョブ更新日時
    """
    id: int
    job_type: str
    target_from: date_type
    target_to: date_type
    status: str  # queued | running | done | failed
    attempts: int
    scheduled_for: Optional[datetime]
    actor: Optional[str]
    payload_json: Optional[dict]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========================================
# Prediction DTOs - 予測結果用DTO
# ========================================

class PredictionDTO(BaseModel):
    """
    日次予測結果
    
    機械学習モデルによる予測値と信頼区間を表現します。
    
    Attributes:
        date: 予測対象日
        y_hat: 予測値（point forecast）
        y_lo: 信頼区間の下限（lower bound）
        y_hi: 信頼区間の上限（upper bound）
        model_version: 使用したモデルのバージョン（例: "v1.2.3"）
        generated_at: 予測を生成した日時
        
    Notes:
        - y_lo, y_hi は信頼区間（例: 95%信頼区間）
        - model_version でモデルのトラッキングが可能
    """
    date: date_type
    y_hat: float = Field(description="Predicted value")
    y_lo: Optional[float] = Field(default=None, description="Lower bound")
    y_hi: Optional[float] = Field(default=None, description="Upper bound")
    model_version: Optional[str] = Field(default=None, description="Model version used")
    generated_at: Optional[datetime] = Field(default=None, description="When prediction was generated")

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ========================================
# Ingest DTOs - データ取り込み用DTO
# ========================================

class ReservationCreate(BaseModel):
    """
    搬入予約作成リクエスト
    
    Attributes:
        date: 予約日（YYYY-MM-DD形式）
        trucks: 予約台数（0以上の整数）
        
    Validation:
        - trucks: 0以上の整数のみ許可（ge=0）
    """
    date: date_type = Field(description="Reservation date (YYYY-MM-DD)")
    trucks: int = Field(ge=0, description="Number of trucks reserved")


class ReservationResponse(BaseModel):
    """
    搬入予約作成レスポンス
    
    Attributes:
        date: 予約日
        trucks: 予約台数
        created_at: 予約作成日時
    """
    date: date_type
    trucks: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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

