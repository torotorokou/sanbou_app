"""
PostgreSQLInboundActualRepository: 日次実績データの取得（DB実装）
================================================================
mart.v_receive_daily から日次実績を取得
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend_shared.application.logging import get_module_logger
from ..ports.inbound_actual_repository import (
    InboundActualRepositoryPort,
    InboundActualDaily
)

logger = get_module_logger(__name__)


class PostgreSQLInboundActualRepository(InboundActualRepositoryPort):
    """PostgreSQL実装の日次実績リポジトリ"""
    
    def __init__(self, session: Session):
        self._session = session
    
    def get_daily_actuals(
        self,
        from_date: date,
        to_date: date,
    ) -> List[InboundActualDaily]:
        """
        mart.v_receive_daily から日次実績を取得
        
        Args:
            from_date: 開始日（この日を含む）
            to_date: 終了日（この日を含む）
        
        Returns:
            List[InboundActualDaily]: 日付昇順のリスト
        """
        query = text("""
            SELECT
                ddate,
                receive_net_ton,
                receive_vehicle_count,
                iso_year,
                iso_week,
                iso_dow,
                is_business,
                is_holiday,
                day_type
            FROM mart.v_receive_daily
            WHERE ddate BETWEEN :from_date AND :to_date
            ORDER BY ddate
        """)
        
        logger.debug(
            f"Fetching inbound actuals: from_date={from_date}, to_date={to_date}"
        )
        
        result = self._session.execute(
            query,
            {"from_date": from_date, "to_date": to_date}
        )
        
        rows = result.fetchall()
        
        logger.info(
            f"Fetched {len(rows)} inbound actual records from mart.v_receive_daily"
        )
        
        return [
            InboundActualDaily(
                ddate=row.ddate,
                receive_net_ton=Decimal(str(row.receive_net_ton)) if row.receive_net_ton is not None else Decimal("0"),
                receive_vehicle_count=int(row.receive_vehicle_count or 0),
                iso_year=int(row.iso_year),
                iso_week=int(row.iso_week),
                iso_dow=int(row.iso_dow),
                is_business=bool(row.is_business),
                is_holiday=bool(row.is_holiday),
                day_type=str(row.day_type),
            )
            for row in rows
        ]
