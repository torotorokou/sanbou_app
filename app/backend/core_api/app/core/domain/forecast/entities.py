"""
Forecast domain entities.
予測ジョブと予測結果のドメインモデル
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
