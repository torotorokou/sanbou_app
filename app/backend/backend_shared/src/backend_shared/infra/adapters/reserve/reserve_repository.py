# app/backend/backend_shared/src/backend_shared/infra/adapters/reserve/reserve_repository.py
"""
PostgreSQL implementation of ReserveRepository.

予約データリポジトリの PostgreSQL 実装。
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend_shared.application.logging import get_module_logger
from backend_shared.core.domain.reserve.entities import ReserveDailyForForecast
from backend_shared.core.domain.reserve.repositories import ReserveRepository
from backend_shared.db.names import SCHEMA_MART, V_RESERVE_DAILY_FOR_FORECAST, fq

logger = get_module_logger(__name__)


class PostgreSQLReserveRepository(ReserveRepository):
    """
    PostgreSQL 用予約データリポジトリ
    
    mart.v_reserve_daily_for_forecast からデータを取得する。
    SELECT ONLY（読み取り専用）。
    
    Args:
        session: SQLAlchemy Session（DIで注入）
    """
    
    def __init__(self, session: Session) -> None:
        self._session = session
    
    def get_reserve_daily_for_forecast(
        self,
        from_date: date,
        to_date: date,
    ) -> list[ReserveDailyForForecast]:
        """
        予測用日次予約データを取得
        
        Args:
            from_date: 開始日（この日を含む）
            to_date: 終了日（この日を含む）
        
        Returns:
            list[ReserveDailyForForecast]: 予約データのリスト（日付昇順）
        
        Raises:
            SQLAlchemyError: DB接続エラー時
        """
        view_name = fq(SCHEMA_MART, V_RESERVE_DAILY_FOR_FORECAST)
        
        query = text(f"""
            SELECT
                date,
                reserve_trucks,
                reserve_fixed_trucks,
                reserve_fixed_ratio,
                source
            FROM {view_name}
            WHERE date BETWEEN :from_date AND :to_date
            ORDER BY date
        """)
        
        logger.debug(
            f"Fetching reserve data from {view_name}: "
            f"from_date={from_date}, to_date={to_date}"
        )
        
        result = self._session.execute(
            query,
            {"from_date": from_date, "to_date": to_date}
        )
        
        rows = result.fetchall()
        
        logger.info(
            f"Fetched {len(rows)} reserve records from {view_name}"
        )
        
        return [
            ReserveDailyForForecast(
                date=row.date,
                reserve_trucks=int(row.reserve_trucks),
                reserve_fixed_trucks=int(row.reserve_fixed_trucks),
                reserve_fixed_ratio=Decimal(str(row.reserve_fixed_ratio)),
                source=row.source,
            )
            for row in rows
        ]
