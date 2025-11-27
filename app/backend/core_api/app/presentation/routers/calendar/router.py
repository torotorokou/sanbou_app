"""
Calendar API Router
営業カレンダーデータの取得エンドポイント

設計方針:
  - Router は HTTP I/O のみを担当
  - ビジネスロジックは UseCase に委譲
  - DI 経由で UseCase を取得
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Dict, Any
import logging

from app.application.usecases.calendar.get_calendar_month_uc import GetCalendarMonthUseCase
from app.config.di_providers import get_calendar_month_uc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/month")
def get_calendar_month(
    year: int = Query(..., ge=1900, le=2100, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month"),
    uc: GetCalendarMonthUseCase = Depends(get_calendar_month_uc),
) -> List[Dict[str, Any]]:
    """
    指定された年月の営業カレンダーデータを取得
    
    Args:
        year: 年 (1900-2100)
        month: 月 (1-12)
        uc: GetCalendarMonthUseCase (DI)
    
    Returns:
        カレンダーデータのリスト
    """
    try:
        data = uc.execute(year, month)
        logger.info(f"Fetched calendar for {year}-{month:02d}: {len(data)} days")
        return data
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Failed to fetch calendar for {year}-{month:02d}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
