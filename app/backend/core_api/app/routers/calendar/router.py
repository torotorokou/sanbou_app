"""
Calendar API Router
営業カレンダーデータの取得エンドポイント
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Dict, Any
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.deps import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/month")
def get_calendar_month(
    year: int = Query(..., ge=1900, le=2100, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    指定された年月の営業カレンダーデータを取得
    
    Args:
        year: 年 (1900-2100)
        month: 月 (1-12)
        db: データベース接続
    
    Returns:
        カレンダーデータのリスト
    """
    sql = text("""
    SELECT ddate, y, m, iso_year, iso_week, iso_dow,
           is_holiday, is_second_sunday, is_company_closed,
           day_type, is_business
    FROM ref.v_calendar_classified
    WHERE y = :year AND m = :month
    ORDER BY ddate
    """)
    
    try:
        result = db.execute(sql, {"year": year, "month": month})
        rows = result.fetchall()
        
        cols = [
            "ddate", "y", "m", "iso_year", "iso_week", "iso_dow",
            "is_holiday", "is_second_sunday", "is_company_closed",
            "day_type", "is_business"
        ]
        
        data = [dict(zip(cols, r)) for r in rows]
        logger.info(f"Fetched calendar for {year}-{month:02d}: {len(data)} days")
        return data
        
    except Exception as e:
        logger.error(f"Failed to fetch calendar for {year}-{month:02d}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
