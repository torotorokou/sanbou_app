"""
Calendar API Router
営業カレンダーデータの取得エンドポイント

Design:
  - Thin router layer (3-step pattern)
  - Query params → Input DTO → UseCase → Output DTO → Response
  - No business logic in this layer
  - Exception handling with custom exceptions
"""
from fastapi import APIRouter, Query, Depends
from typing import List, Dict, Any
import logging

from app.core.usecases.calendar.get_calendar_month_uc import GetCalendarMonthUseCase
from app.core.usecases.calendar.dto import GetCalendarMonthInput
from app.config.di_providers import get_calendar_month_uc
from backend_shared.core.domain.exceptions import ValidationError, InfrastructureError

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
    
    Follows Clean Architecture with 3-step pattern:
      1. Query params → Input DTO
      2. UseCase execution
      3. Output DTO → Response
    
    Args:
        year: 年 (1900-2100)
        month: 月 (1-12)
        uc: GetCalendarMonthUseCase (DI)
    
    Returns:
        カレンダーデータのリスト
    """
    try:
        # Step 1: Query params → Input DTO
        input_dto = GetCalendarMonthInput(year=year, month=month)
        
        # Step 2: UseCase execution
        output_dto = uc.execute(input_dto)
        
        # Step 3: Output DTO → Response
        logger.info(f"Fetched calendar for {year}-{month:02d}: {len(output_dto.calendar_days)} days")
        return output_dto.calendar_days
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise ValidationError(message=str(e), field="year_or_month")
        
    except Exception as e:
        logger.error(f"Failed to fetch calendar for {year}-{month:02d}: {e}", exc_info=True)
        raise InfrastructureError(message=f"Calendar data retrieval failed: {str(e)}", cause=e)
