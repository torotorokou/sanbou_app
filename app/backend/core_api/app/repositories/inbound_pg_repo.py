# -*- coding: utf-8 -*-
"""
Inbound repository implementation with PostgreSQL.
日次搬入量データの取得（CTE + ウィンドウ関数で累積計算）
"""
from datetime import date as date_type
from typing import List, Optional
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.inbound_repository_port import InboundRepository
from app.domain.inbound import InboundDailyRow, CumScope

# 👇 SQL識別子は1か所で管理（定数化）
from app.repositories.sql_names import V_RECEIVE_DAILY, V_CALENDAR

logger = logging.getLogger(__name__)

ALLOWED_CUM_SCOPES = {"none", "range", "month", "week"}


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
        1. CTE 'd': カレンダー({V_CALENDAR})と入荷ビュー({V_RECEIVE_DAILY})をLEFT JOINし、欠損日を0埋め
        2. 本体: cum_scopeに応じてウィンドウ関数で累積値を付与
        3. 連続日・0埋め済みの日次データを返却

        Args:
            start: 開始日（含む）
            end:   終了日（含む）
            segment: セグメントフィルタ（現状このビューには列が無いため未使用）
            cum_scope: 累積スコープ（"range"=全期間, "month"=月ごと, "week"=週ごと, "none"=累積なし）

        Returns:
            List[InboundDailyRow]

        Raises:
            ValueError: start > end、または範囲が366日を超える、またはcum_scopeが不正
        """
        # --- Validation ---
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")
        delta_days = (end - start).days + 1
        if delta_days > 366:
            raise ValueError(f"Date range exceeds 366 days: {delta_days} days")
        if cum_scope not in ALLOWED_CUM_SCOPES:
            raise ValueError(
                f"Invalid cum_scope: {cum_scope}. Must be one of {sorted(ALLOWED_CUM_SCOPES)}"
            )

        # 現時点のv_receive_dailyにはsegment列がないため、受け取っても無視（将来対応用）
        if segment is not None:
            logger.warning("segment filter is not supported on %s; ignoring segment=%r",
                           V_RECEIVE_DAILY, segment)

        # --- SQL with CTE + window function ---
        # 識別子（ビュー名など）は f-string で差し込み、値はバインドパラメータで渡す
        sql = text(f"""
WITH d AS (
  SELECT
    c.ddate,
    c.iso_year,
    c.iso_week,
    c.iso_dow,
    c.is_business,
    COALESCE(r.receive_net_ton, 0)::numeric AS ton
  FROM {V_CALENDAR} AS c
  LEFT JOIN {V_RECEIVE_DAILY} AS r
    ON r.ddate = c.ddate
  WHERE c.ddate BETWEEN :start AND :end
)
SELECT
  d.ddate,
  d.iso_year,
  d.iso_week,
  d.iso_dow,
  d.is_business,
  NULL::text AS segment,  -- 互換のため形だけ返す（将来segment対応時に置換）
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

            data: List[InboundDailyRow] = []
            for r in rows:
                # rのポジションはSELECT順に対応
                ddate = r[0]
                iso_year = r[1]
                iso_week = r[2]
                iso_dow = r[3]
                is_business = r[4]
                seg = r[5]  # 現状はNone相当の文字列NULL::text
                ton = float(r[6]) if r[6] is not None else 0.0
                cum = float(r[7]) if r[7] is not None else None

                data.append(
                    InboundDailyRow(
                        ddate=ddate,
                        iso_year=iso_year,
                        iso_week=iso_week,
                        iso_dow=iso_dow,
                        is_business=is_business,
                        segment=seg,
                        ton=ton,
                        cum_ton=cum,
                    )
                )

            logger.info(
                "Fetched %d daily rows: %s to %s, segment=%s, cum_scope=%s",
                len(data), start, end, segment, cum_scope
            )
            return data

        except Exception as e:
            logger.error(
                "Failed to fetch daily inbound: %s to %s, segment=%s, cum_scope=%s, error=%s",
                start, end, segment, cum_scope, e,
                exc_info=True,
            )
            raise
