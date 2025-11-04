"""
Inbound repository implementation with PostgreSQL.
日次搬入量データの取得（CTE + ウィンドウ関数で累積計算）
"""
from datetime import date as date_type
from typing import List, Optional
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ports.inbound_repository import InboundRepository
from app.domain.inbound import InboundDailyRow, CumScope


logger = logging.getLogger(__name__)


class InboundPgRepository(InboundRepository):
    """
    PostgreSQL implementation of InboundRepository.
    CTE + ウィンドウ関数で連続日・0埋め・累積計算を実現
    """

    def __init__(self, db: Session):
        self.db = db

    def fetch_daily(
        self,
        start: date_type,
        end: date_type,
        segment: Optional[str] = None,
        cum_scope: CumScope = "none",
    ) -> List[InboundDailyRow]:
        """
        Fetch daily inbound data with calendar continuity and optional cumulative calculation.
        
        Logic:
        1. CTE 'd': LEFT JOIN calendar with mart.receive_daily to ensure all dates present
        2. CTE 'cum': Apply window function based on cum_scope
        3. Return zero-filled continuous daily data with optional cumulative values
        
        Args:
            start: 開始日
            end: 終了日
            segment: セグメントフィルタ（None=全体）
            cum_scope: 累積スコープ（"range"=全期間, "month"=月ごと, "week"=週ごと, "none"=累積なし）
        
        Returns:
            連続日・0埋め済み日次搬入量データのリスト
        
        Raises:
            ValueError: start > end, または範囲が365日を超える場合
        """
        # Validation
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")
        delta_days = (end - start).days + 1
        if delta_days > 366:
            raise ValueError(f"Date range exceeds 366 days: {delta_days} days")

        # SQL with CTE + window function (segment機能なし版)
        sql = text("""
WITH d AS (
  SELECT
    c.ddate,
    c.iso_year,
    c.iso_week,
    c.iso_dow,
    c.is_business,
    COALESCE(r.receive_net_ton, 0)::numeric AS ton
  FROM ref.v_calendar_classified c
  LEFT JOIN mart.receive_daily r
    ON r.ddate = c.ddate
  WHERE c.ddate BETWEEN :start AND :end
)
SELECT
  d.ddate,
  d.iso_year,
  d.iso_week,
  d.iso_dow,
  d.is_business,
  NULL::text AS segment,
  d.ton,
  CASE
    WHEN :cum_scope = 'range' THEN
      SUM(d.ton) OVER (
        ORDER BY d.ddate
        ROWS UNBOUNDED PRECEDING
      )
    WHEN :cum_scope = 'month' THEN
      SUM(d.ton) OVER (
        PARTITION BY DATE_TRUNC('month', d.ddate)
        ORDER BY d.ddate
        ROWS UNBOUNDED PRECEDING
      )
    WHEN :cum_scope = 'week' THEN
      SUM(d.ton) OVER (
        PARTITION BY d.iso_year, d.iso_week
        ORDER BY d.ddate
        ROWS UNBOUNDED PRECEDING
      )
    ELSE NULL
  END AS cum_ton
FROM d
ORDER BY d.ddate
        """)

        try:
            result = self.db.execute(
                sql,
                {
                    "start": start,
                    "end": end,
                    "cum_scope": cum_scope,
                },
            )
            rows = result.fetchall()
            
            data = [
                InboundDailyRow(
                    ddate=r[0],
                    iso_year=r[1],
                    iso_week=r[2],
                    iso_dow=r[3],
                    is_business=r[4],
                    segment=r[5],
                    ton=float(r[6]),
                    cum_ton=float(r[7]) if r[7] is not None else None,
                )
                for r in rows
            ]
            
            logger.info(
                f"Fetched {len(data)} daily rows: {start} to {end}, "
                f"segment={segment}, cum_scope={cum_scope}"
            )
            return data

        except Exception as e:
            logger.error(
                f"Failed to fetch daily inbound: {start} to {end}, "
                f"segment={segment}, cum_scope={cum_scope}, error={e}",
                exc_info=True,
            )
            raise
