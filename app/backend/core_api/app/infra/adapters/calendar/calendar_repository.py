"""
Calendar Repository - カレンダーデータ取得の PostgreSQL 実装

implements Port: ICalendarQuery
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class CalendarRepository:
    """
    カレンダーデータ取得リポジトリ（PostgreSQL実装）
    
    ref.v_calendar_classified ビューから営業カレンダー情報を取得します。
    """
    
    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy セッション
        """
        self.db = db
    
    def get_month_calendar(self, year: int, month: int) -> List[Dict[str, Any]]:
        """
        指定された年月のカレンダーデータを取得
        
        Args:
            year: 年 (1900-2100)
            month: 月 (1-12)
            
        Returns:
            カレンダーデータのリスト（日付順ソート済み）
            
        Raises:
            Exception: SQLエラー時
        """
        sql = text("""
        SELECT ddate, y, m, iso_year, iso_week, iso_dow,
               is_holiday, is_second_sunday, is_company_closed,
               day_type, is_business
        FROM ref.v_calendar_classified
        WHERE y = :year AND m = :month
        ORDER BY ddate
        """)
        
        result = self.db.execute(sql, {"year": year, "month": month})
        rows = result.fetchall()
        
        # カラム名リスト
        cols = [
            "ddate", "y", "m", "iso_year", "iso_week", "iso_dow",
            "is_holiday", "is_second_sunday", "is_company_closed",
            "day_type", "is_business"
        ]
        
        # 辞書形式に変換
        data = [dict(zip(cols, r)) for r in rows]
        
        logger.debug(f"Fetched calendar for {year}-{month:02d}: {len(data)} days")
        
        return data
