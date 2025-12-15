"""
API Schemas - Request/Response models

Pydanticモデルによるリクエスト/レスポンスの定義。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """予測リクエスト"""
    future_days: int = Field(default=7, description="予測日数", ge=1, le=90)
    start_date: Optional[str] = Field(default=None, description="開始日 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="終了日 (YYYY-MM-DD)")


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str = "healthy"
    service: str = "inbound_forecast_api"
    timestamp: datetime
