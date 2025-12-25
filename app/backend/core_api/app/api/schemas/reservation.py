"""
Reservation Schemas - 予約関連のスキーマ定義

Presentation Layer: HTTP Request/Response schemas
"""

from datetime import date as date_type
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# ========================================
# Manual Reservation DTOs
# ========================================


class ReservationManualInput(BaseModel):
    """手入力の予約データ (Upsert用)"""

    reserve_date: date_type = Field(description="予約日")
    total_trucks: int = Field(ge=0, description="合計台数")
    fixed_trucks: int = Field(ge=0, description="固定客台数")
    note: Optional[str] = Field(default=None, description="メモ")

    model_config = ConfigDict(from_attributes=True)


class ReservationManualResponse(BaseModel):
    """手入力の予約データ (Response)"""

    reserve_date: date_type
    total_trucks: int
    fixed_trucks: int
    note: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========================================
# Forecast View DTOs
# ========================================


class ReservationForecastDaily(BaseModel):
    """予測用の日次予約データ (mart.v_reserve_daily_for_forecast)"""

    date: date_type = Field(description="予約日")
    reserve_trucks: int = Field(description="予約台数合計")
    reserve_fixed_trucks: int = Field(description="固定客台数")
    reserve_fixed_ratio: float = Field(description="固定客比率")
    source: Literal["manual", "customer_agg"] = Field(description="データソース")

    model_config = ConfigDict(from_attributes=True)


# ========================================
# Customer Reservation DTOs
# ========================================


class ReservationCustomerDailyInput(BaseModel):
    """顧客別予約データ (Upsert用)"""

    reserve_date: date_type = Field(description="予約日")
    customer_cd: str = Field(description="顧客コード")
    customer_name: Optional[str] = Field(default=None, description="顧客名")
    planned_trucks: int = Field(ge=0, description="予定台数")
    is_fixed_customer: bool = Field(default=False, description="固定客フラグ")
    note: Optional[str] = Field(default=None, description="メモ")

    model_config = ConfigDict(from_attributes=True)


class ReservationCustomerDailyResponse(BaseModel):
    """顧客別予約データ (Response)"""

    id: int
    reserve_date: date_type
    customer_cd: str
    customer_name: Optional[str] = None
    planned_trucks: int
    is_fixed_customer: bool
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
