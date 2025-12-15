"""
Prediction domain entities.
予測リクエストと予測結果のドメインモデル
"""
from datetime import date as date_type
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DailyForecastRequest(BaseModel):
    """
    日次予測リクエスト
    
    Attributes:
        target_date: 予測対象日（Noneの場合は明日）
        model_version: 使用するモデルバージョン（Noneの場合はデフォルト）
        
    Example:
        # 明日の予測
        request = DailyForecastRequest()
        
        # 特定日の予測
        request = DailyForecastRequest(
            target_date=date(2025, 1, 22),
            model_version="v1_daily_tplus1"
        )
    """
    target_date: Optional[date_type] = Field(
        default=None,
        description="予測対象日（Noneの場合は明日）"
    )
    model_version: Optional[str] = Field(
        default=None,
        description="使用するモデルバージョン（Noneの場合はデフォルト）"
    )
    
    model_config = ConfigDict(
        frozen=True,  # イミュータブル
        protected_namespaces=(),  # model_ プレフィックスを許可
        json_schema_extra={
            "example": {
                "target_date": "2025-01-22",
                "model_version": "v1_daily_tplus1"
            }
        }
    )


class PredictionResult(BaseModel):
    """
    予測結果
    
    機械学習モデルによる日次予測値と信頼区間を表現します。
    
    Attributes:
        prediction_date: 予測対象日
        y_hat: 予測値（point forecast）- 搬入量トン数
        y_lo: 信頼区間の下限（lower bound）
        y_hi: 信頼区間の上限（upper bound）
        model_version: 使用したモデルのバージョン
        
    Notes:
        - y_lo, y_hi は信頼区間（例: 95%信頼区間）
        - model_version でモデルのトラッキングが可能
    """
    prediction_date: date_type = Field(description="予測対象日")
    y_hat: float = Field(description="予測値（搬入量トン数）", ge=0)
    y_lo: Optional[float] = Field(
        default=None,
        description="信頼区間下限",
        ge=0
    )
    y_hi: Optional[float] = Field(
        default=None,
        description="信頼区間上限",
        ge=0
    )
    model_version: Optional[str] = Field(
        default=None,
        description="使用したモデルバージョン"
    )
    
    model_config = ConfigDict(
        frozen=True,  # イミュータブル
        protected_namespaces=(),  # model_ プレフィックスを許可
        json_schema_extra={
            "example": {
                "prediction_date": "2025-01-22",
                "y_hat": 91384.19,
                "y_lo": 80155.54,
                "y_hi": 102612.84,
                "model_version": "v1_daily_tplus1"
            }
        }
    )


class PredictionOutput(BaseModel):
    """
    予測実行の出力
    
    予測実行の結果として生成されるファイルパスと予測データを含みます。
    
    Attributes:
        csv_path: 生成されたCSVファイルのパス
        predictions: 予測結果のリスト（オプション）
        
    Notes:
        - csv_pathは常に返却される（既存システムとの互換性）
        - predictionsは将来的にAPI化する際に使用
    """
    csv_path: str = Field(description="生成されたCSVファイルのパス")
    predictions: Optional[list[PredictionResult]] = Field(
        default=None,
        description="予測結果のリスト（オプション）"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "csv_path": "/backend/output/tplus1_pred_20251215_142253.csv",
                "predictions": [
                    {
                        "prediction_date": "2025-01-22",
                        "y_hat": 91384.19,
                        "y_lo": 80155.54,
                        "y_hi": 102612.84,
                        "model_version": "v1_daily_tplus1"
                    }
                ]
            }
        }
    )
