"""
Prediction domain package.
予測リクエストと予測結果のドメインモデル
"""
from app.core.domain.prediction.entities import (
    DailyForecastRequest,
    PredictionResult,
    PredictionOutput,
)

__all__ = [
    "DailyForecastRequest",
    "PredictionResult",
    "PredictionOutput",
]
