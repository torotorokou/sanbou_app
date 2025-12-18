"""
PostgreSQLReserveDailyRepository: 予約データの取得（DB実装）
==========================================================
mart.v_reserve_daily_for_forecast から予約データを取得
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend_shared.application.logging import get_module_logger
from ..ports.reserve_daily_repository import (
    ReserveDailyRepositoryPort,
    ReserveDailyForForecast
)

logger = get_module_logger(__name__)


class PostgreSQLReserveDailyRepository(ReserveDailyRepositoryPort):
    """PostgreSQL実装の予約データリポジトリ"""
    
    def __init__(self, session: Session):
        self._session = session
    
    def get_reserve_daily(
        self,
        from_date: date,
        to_date: date,
    ) -> List[ReserveDailyForForecast]:
        """
        mart.v_reserve_daily_for_forecast から予約データを取得
        
        Args:
            from_date: 開始日（この日を含む）
            to_date: 終了日（この日を含む）
        
        Returns:
            List[ReserveDailyForForecast]: 日付昇順のリスト（データが無い日は含まれない）
        """
        query = text("""
            SELECT
                date,
                reserve_trucks,
                reserve_fixed_trucks,
                reserve_fixed_ratio,
                source
            FROM mart.v_reserve_daily_for_forecast
            WHERE date BETWEEN :from_date AND :to_date
            ORDER BY date
        """)
        
        logger.debug(
            f"Fetching reserve data: from_date={from_date}, to_date={to_date}"
        )
        
        result = self._session.execute(
            query,
            {"from_date": from_date, "to_date": to_date}
        )
        
        rows = result.fetchall()
        
        logger.info(
            f"Fetched {len(rows)} reserve records from mart.v_reserve_daily_for_forecast"
        )
        
        return [
            ReserveDailyForForecast(
                date=row.date,
                reserve_trucks=int(row.reserve_trucks or 0),
                reserve_fixed_trucks=int(row.reserve_fixed_trucks or 0),
                reserve_fixed_ratio=Decimal(str(row.reserve_fixed_ratio)) if row.reserve_fixed_ratio is not None else Decimal("0"),
                source=str(row.source),
            )
            for row in rows
        ]
