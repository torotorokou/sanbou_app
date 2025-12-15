"""
Ingest domain entities.
データ取り込み（搬入予約）のドメインモデル
"""
from datetime import date as date_type, datetime
from pydantic import BaseModel, Field, ConfigDict


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
