"""
Prediction Router

需要予測に関するAPIエンドポイント。
Router層では、リクエストの受け取り、UseCaseの呼び出し、レスポンスの返却のみを行う。
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.api.schemas.prediction import PredictionRequest, HealthResponse

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    ヘルスチェックエンドポイント
    
    Returns:
        HealthResponse: サービスのステータス
    """
    return HealthResponse(
        status="healthy",
        service="inbound_forecast_api",
        timestamp=datetime.now(),
    )


@router.get("/")
async def root():
    """
    ルートエンドポイント
    
    Returns:
        dict: サービス情報
    """
    return {
        "service": "inbound_forecast_api",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "predict": "/api/v1/predict (未実装)",
        },
    }


@router.post("/api/v1/predict")
async def predict(request: PredictionRequest):
    """
    需要予測エンドポイント（未実装）
    
    Args:
        request: 予測リクエスト
        
    Returns:
        dict: 予測結果（将来実装予定）
        
    Raises:
        HTTPException: 501 Not Implemented
    """
    logger.info(f"Prediction request: {request}")
    
    # TODO: UseCaseをDIで受け取り、実行する
    # usecase = Depends(get_prediction_usecase)
    # result = usecase.execute(request)
    # return result
    
    raise HTTPException(
        status_code=501,
        detail="Prediction endpoint not yet implemented. This is a placeholder for future development.",
    )
