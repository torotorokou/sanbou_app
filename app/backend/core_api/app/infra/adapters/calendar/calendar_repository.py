"""
Calendar Repository - カレンダーデータ取得の PostgreSQL 実装

implements Port: ICalendarQuery
"""

import logging
from typing import Any, Dict, List

from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.db.names import SCHEMA_REF, V_CALENDAR_CLASSIFIED, fq
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = get_module_logger(__name__)


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
        sql = text(
            f"""
        SELECT ddate, y, m, iso_year, iso_week, iso_dow,
               is_holiday, is_second_sunday, is_company_closed,
               day_type, is_business
        FROM {fq(SCHEMA_REF, V_CALENDAR_CLASSIFIED)}
        WHERE y = :year AND m = :month
        ORDER BY ddate
        """
        )

        result = self.db.execute(sql, {"year": year, "month": month})
        rows = result.fetchall()

        # カラム名リスト
        cols = [
            "ddate",
            "y",
            "m",
            "iso_year",
            "iso_week",
            "iso_dow",
            "is_holiday",
            "is_second_sunday",
            "is_company_closed",
            "day_type",
            "is_business",
        ]

        # 辞書形式に変換
        data = [dict(zip(cols, r)) for r in rows]

        logger.debug(
            "カレンダー取得",
            extra=create_log_context(
                operation="get_month_calendar",
                year=year,
                month=month,
                days_count=len(data),
            ),
        )

        return data
