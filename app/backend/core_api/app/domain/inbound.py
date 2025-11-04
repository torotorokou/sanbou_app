"""
Inbound domain entities and value objects.
日次搬入量データのドメインエンティティ
"""
from datetime import date as date_type
from typing import Optional, Literal
from pydantic import BaseModel, Field


# Cumulative scope literal type
CumScope = Literal["range", "month", "week", "none"]


class InboundDailyRow(BaseModel):
    """
    日次搬入量データ（カレンダー連続・0埋め済み）
    
    Fields:
        ddate: 日付
        iso_year: ISO年
        iso_week: ISO週番号
        iso_dow: ISO曜日（1=月, 7=日）
        is_business: 営業日フラグ
        segment: セグメント（オプション）
        ton: 日次搬入量トン数（欠損日は0）
        cum_ton: 累積搬入量トン数（cum_scope指定時のみ計算）
    """
    ddate: date_type = Field(..., description="日付")
    iso_year: int = Field(..., description="ISO年")
    iso_week: int = Field(..., description="ISO週番号")
    iso_dow: int = Field(..., ge=1, le=7, description="ISO曜日（1=月, 7=日）")
    is_business: bool = Field(..., description="営業日フラグ")
    segment: Optional[str] = Field(None, description="セグメント")
    ton: float = Field(..., ge=0, description="日次搬入量トン数")
    cum_ton: Optional[float] = Field(None, ge=0, description="累積搬入量トン数")

    class Config:
        json_schema_extra = {
            "example": {
                "ddate": "2025-10-15",
                "iso_year": 2025,
                "iso_week": 42,
                "iso_dow": 3,
                "is_business": True,
                "segment": None,
                "ton": 125.5,
                "cum_ton": 1850.2,
            }
        }
