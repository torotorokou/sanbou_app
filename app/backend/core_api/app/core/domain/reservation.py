"""
Reservation domain entities.
予約データのドメインエンティティ
"""

from datetime import date as date_type
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ReservationManualRow(BaseModel):
    """
    手入力の日次予約合計データ (stg.reserve_daily_manual)

    Fields:
        reserve_date: 予約日 (PK)
        total_trucks: 合計台数
        fixed_trucks: 固定客台数
        note: メモ（オプション）
        created_by: 作成者（オプション）
        updated_by: 更新者（オプション）
        created_at: 作成日時（オプション、DBで設定）
        updated_at: 更新日時（オプション、DBで設定）
    """

    reserve_date: date_type = Field(..., description="予約日")
    total_trucks: int = Field(..., ge=0, description="合計台数")
    fixed_trucks: int = Field(..., ge=0, description="固定客台数")
    note: Optional[str] = Field(None, description="メモ")
    created_by: Optional[str] = Field(None, description="作成者")
    updated_by: Optional[str] = Field(None, description="更新者")
    created_at: Optional[datetime] = Field(None, description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")

    class Config:
        from_attributes = True


class ReservationForecastRow(BaseModel):
    """
    予測用の日次予約データ (mart.v_reserve_daily_for_forecast)

    manual優先、なければcustomer集計

    Fields:
        date: 予約日
        reserve_trucks: 予約台数合計
        reserve_fixed_trucks: 固定客台数
        reserve_fixed_ratio: 固定客比率
        source: データソース ('manual' | 'customer_agg')
    """

    date: date_type = Field(..., description="予約日")
    reserve_trucks: int = Field(..., description="予約台数合計")
    reserve_fixed_trucks: int = Field(..., description="固定客台数")
    reserve_fixed_ratio: float = Field(..., description="固定客比率")
    source: Literal["manual", "customer_agg"] = Field(..., description="データソース")

    class Config:
        from_attributes = True


class ReservationCustomerRow(BaseModel):
    """
    顧客別予約データ (stg.reserve_customer_daily)

    Fields:
        id: ID (PK)
        reserve_date: 予約日
        customer_cd: 顧客コード
        customer_name: 顧客名（オプション）
        planned_trucks: 予定台数
        is_fixed_customer: 固定客フラグ
        note: メモ（オプション）
        created_at: 作成日時（オプション）
        updated_at: 更新日時（オプション）
    """

    id: Optional[int] = Field(None, description="ID")
    reserve_date: date_type = Field(..., description="予約日")
    customer_cd: str = Field(..., description="顧客コード")
    customer_name: Optional[str] = Field(None, description="顧客名")
    planned_trucks: int = Field(..., ge=0, description="予定台数")
    is_fixed_customer: bool = Field(..., description="固定客フラグ")
    note: Optional[str] = Field(None, description="メモ")
    created_at: Optional[datetime] = Field(None, description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")

    class Config:
        from_attributes = True
