"""
Dashboard router: target metrics and dashboard data.

設計方針:
  - Router は HTTP I/O のみ
  - ビジネスロジックは UseCase に委譲
  - DI 経由で UseCase を取得
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import date as date_type
from typing import Literal
import logging

from app.deps import get_db
from app.config.di_providers import get_build_target_card_uc
from app.application.usecases.dashboard.build_target_card_uc import BuildTargetCardUseCase
from app.presentation.schemas import TargetMetricsResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/target", response_model=TargetMetricsResponse, summary="Get target and actual metrics")
def get_target_metrics(
    date: date_type = Query(..., description="Target date (YYYY-MM-DD). For monthly view, use first day of month."),
    mode: Literal["daily", "monthly"] = Query("monthly", description="Fetch mode: 'daily' for specific date, 'monthly' for month-level view with day/week masking"),
    uc: BuildTargetCardUseCase = Depends(get_build_target_card_uc),
):
    """
    Retrieve monthly, weekly, and daily target metrics with actuals for the specified date.
    
    **Anchor Date Resolution:**
    - Current month: Uses today as anchor
    - Past month: Uses last day of month as anchor
    - Future month: Uses first business day of month as anchor
    
    **NULL Masking (mode='monthly' only):**
    - For past/future months, day_target_ton, week_target_ton, day_actual_ton_prev, and week_actual_ton are set to null
    - Frontend should display "—" for null values
    
    **Usage Examples:**
    - Current month monthly view: `?date=2025-10-01&mode=monthly` → fetches today's data
    - Past month monthly view: `?date=2025-09-01&mode=monthly` → fetches 2025-09-30 data with day/week masked
    - Future month monthly view: `?date=2025-12-01&mode=monthly` → fetches first business day with day/week masked
    - Specific day view: `?date=2025-10-15&mode=daily` → fetches 2025-10-15 data without masking
    """
    try:
        logger.info(f"GET /dashboard/target called with date={date}, mode={mode}")
        
        data = uc.execute(date, mode=mode)  # type: ignore[arg-type]
        
        if not data:
            logger.warning(f"No target card data found for date={date}, mode={mode}")
            raise HTTPException(
                status_code=404,
                detail=f"No target card data found for {date}. Please check if mart.v_target_card_per_day has data for this period."
            )
        
        logger.info(f"Successfully retrieved target metrics for date={date}, mode={mode}")
        return TargetMetricsResponse(**data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving target metrics for date={date}, mode={mode}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching target metrics: {str(e)}"
        )


