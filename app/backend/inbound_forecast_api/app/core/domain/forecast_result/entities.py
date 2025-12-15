"""
Forecast Result Domain Entities

予測結果のドメインエンティティ定義。
"""
from datetime import date as DateType
from typing import Optional, List
from pydantic import BaseModel, Field


class ForecastResultRecord(BaseModel):
    """
    予測結果の1レコード
    
    共通フィールド:
    - date: 予測対象日
    - predicted_value: 予測値
    - confidence_lower: 信頼区間下限（オプション）
    - confidence_upper: 信頼区間上限（オプション）
    """
    date: DateType = Field(..., description="予測対象日")
    predicted_value: float = Field(..., description="予測値")
    confidence_lower: Optional[float] = Field(None, description="信頼区間下限")
    confidence_upper: Optional[float] = Field(None, description="信頼区間上限")
    
    # 追加メトリクス（モデルによって異なる）
    p50: Optional[float] = Field(None, description="中央値")
    p90: Optional[float] = Field(None, description="90パーセンタイル")
    raw_data: Optional[dict] = Field(None, description="生データ（CSV全カラム）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-12-15",
                "predicted_value": 91384.19,
                "confidence_lower": 80155.54,
                "confidence_upper": 102612.84,
                "p50": 58849.39,
                "p90": 30401.43,
            }
        }


class ForecastResult(BaseModel):
    """
    予測結果セット
    
    モデルタイプごとの予測結果をまとめたもの。
    """
    model_type: str = Field(..., description="モデルタイプ (daily/monthly/weekly/landing)")
    generated_at: Optional[DateType] = Field(None, description="予測生成日時")
    records: List[ForecastResultRecord] = Field(default_factory=list, description="予測レコード")
    
    # メタデータ
    model_version: Optional[str] = Field(None, description="モデルバージョン")
    csv_path: Optional[str] = Field(None, description="元CSVファイルパス")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_type": "daily",
                "generated_at": "2025-12-15",
                "records": [
                    {
                        "date": "2025-12-16",
                        "predicted_value": 91384.19,
                        "confidence_lower": 80155.54,
                        "confidence_upper": 102612.84,
                    }
                ],
                "model_version": "v1_daily_tplus1",
            }
        }


class ForecastResultNotFound(BaseModel):
    """
    予測結果が見つからない場合のレスポンス
    """
    model_type: str
    message: str = "予測結果がまだ生成されていません"
    csv_path: Optional[str] = None
