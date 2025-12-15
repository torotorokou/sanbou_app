"""
Forecast Results API Router

予測結果の閲覧専用API（Phase 1）

設計方針:
- Router責務: 入出力のみ（検証・変換・HTTPレスポンス生成）
- ビジネスロジックはUseCaseに委譲
- UseCaseはDIで注入（new禁止）
- SQLクエリ禁止
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.usecases.get_forecast_result_uc import GetForecastResultUseCase
from app.core.domain.forecast_result import ForecastResult, ForecastResultNotFound
from app.config.di_providers import get_forecast_result_usecase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/forecast/results",
    tags=["forecast-results"],
)


@router.get("/daily", response_model=ForecastResult)
def get_daily_forecast_result(
    usecase: GetForecastResultUseCase = Depends(get_forecast_result_usecase),
) -> ForecastResult:
    """
    日次予測結果を取得（t+1/t+7）
    
    Returns:
        ForecastResult: 日次予測結果
    
    Raises:
        HTTPException(404): 予測結果が見つからない
        HTTPException(500): 内部エラー
    """
    logger.info("GET /forecast/results/daily")
    
    try:
        result = usecase.get_daily()
        
        if result is None:
            logger.warning("Daily forecast result not found")
            raise HTTPException(
                status_code=404,
                detail="Daily forecast result not found. Please run prediction first.",
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get daily forecast result: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        ) from e


@router.get("/monthly", response_model=ForecastResult)
def get_monthly_forecast_result(
    usecase: GetForecastResultUseCase = Depends(get_forecast_result_usecase),
) -> ForecastResult:
    """
    月次予測結果を取得（Gamma Recency + Blend）
    
    Returns:
        ForecastResult: 月次予測結果
    
    Raises:
        HTTPException(404): 予測結果が見つからない
        HTTPException(500): 内部エラー
    """
    logger.info("GET /forecast/results/monthly")
    
    try:
        result = usecase.get_monthly()
        
        if result is None:
            logger.warning("Monthly forecast result not found")
            raise HTTPException(
                status_code=404,
                detail="Monthly forecast result not found. Please run prediction first.",
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get monthly forecast result: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        ) from e


@router.get("/weekly", response_model=ForecastResult)
def get_weekly_forecast_result(
    usecase: GetForecastResultUseCase = Depends(get_forecast_result_usecase),
) -> ForecastResult:
    """
    週次予測結果を取得（週次配分）
    
    Returns:
        ForecastResult: 週次予測結果
    
    Raises:
        HTTPException(404): 予測結果が見つからない
        HTTPException(500): 内部エラー
    """
    logger.info("GET /forecast/results/weekly")
    
    try:
        result = usecase.get_weekly()
        
        if result is None:
            logger.warning("Weekly forecast result not found")
            raise HTTPException(
                status_code=404,
                detail="Weekly forecast result not found. Please run prediction first.",
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get weekly forecast result: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        ) from e


@router.get("/landing", response_model=ForecastResult)
def get_landing_forecast_result(
    day: int = Query(14, ge=14, le=21, description="着地予測日数（14 or 21）"),
    usecase: GetForecastResultUseCase = Depends(get_forecast_result_usecase),
) -> ForecastResult:
    """
    月次着地予測結果を取得（14日/21日）
    
    Args:
        day: 着地予測日数（14 or 21）
    
    Returns:
        ForecastResult: 着地予測結果
    
    Raises:
        HTTPException(400): 無効なパラメータ
        HTTPException(404): 予測結果が見つからない
        HTTPException(500): 内部エラー
    """
    logger.info(f"GET /forecast/results/landing?day={day}")
    
    # パラメータ検証
    if day not in (14, 21):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid day parameter: {day}. Must be 14 or 21.",
        )
    
    try:
        result = usecase.get_landing(day=day)
        
        if result is None:
            logger.warning(f"Landing forecast result not found (day={day})")
            raise HTTPException(
                status_code=404,
                detail=f"Landing forecast result not found for {day} days. Please run prediction first.",
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get landing forecast result: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        ) from e
