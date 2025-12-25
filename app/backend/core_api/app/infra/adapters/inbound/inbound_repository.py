# -*- coding: utf-8 -*-
"""
Inbound repository implementation with PostgreSQL.
日次搬入量データの取得（CTE + ウィンドウ関数で累積計算）
"""
import logging
from datetime import date as date_type
from typing import List, Optional

from app.core.domain.inbound import CumScope, InboundDailyRow
from app.core.ports.inbound_repository_port import InboundRepository
from app.infra.db.sql_loader import load_sql
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.db.names import (
    MV_RECEIVE_DAILY,
    SCHEMA_MART,
    SCHEMA_REF,
    V_CALENDAR_CLASSIFIED,
    fq,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = get_module_logger(__name__)

ALLOWED_CUM_SCOPES = {"none", "range", "month", "week"}


class InboundRepositoryImpl(InboundRepository):
    """
    PostgreSQL implementation of InboundRepository.
    CTE + ウィンドウ関数で連続日・0埋め・累積計算を実現
    """

    def __init__(self, db: Session):
        self.db = db
        # Pre-load SQL for get_daily_with_cumulative (legacy, kept for compatibility)
        template = load_sql(
            "inbound/inbound_pg_repository__get_daily_with_cumulative.sql"
        )
        self._daily_cumulative_sql = text(
            template.format(
                v_calendar=fq(SCHEMA_REF, V_CALENDAR_CLASSIFIED),
                mv_receive_daily=fq(SCHEMA_MART, MV_RECEIVE_DAILY),
            )
        )
        # Pre-load SQL for get_daily_with_comparisons (new: includes prev_month/prev_year)
        template = load_sql(
            "inbound/inbound_pg_repository__get_daily_with_comparisons.sql"
        )
        self._daily_comparisons_sql = text(
            template.format(
                v_calendar=fq(SCHEMA_REF, V_CALENDAR_CLASSIFIED),
                mv_receive_daily=fq(SCHEMA_MART, MV_RECEIVE_DAILY),
            )
        )
        # 案6: Simplified query without comparisons (for performance)
        template = load_sql("inbound/inbound_pg_repository__get_daily_simple.sql")
        self._daily_simple_sql = text(
            template.format(
                v_calendar=fq(SCHEMA_REF, V_CALENDAR_CLASSIFIED),
                mv_receive_daily=fq(SCHEMA_MART, MV_RECEIVE_DAILY),
            )
        )

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

        # 現時点のmv_receive_dailyにはsegment列がないため、受け取っても無視（将来対応用）
        if segment is not None:
            logger.warning(
                "segment filter is not supported on %s; ignoring segment=%r",
                fq(SCHEMA_MART, MV_RECEIVE_DAILY),
                segment,
            )

        # --- SQL with CTE + window function (loaded from external file) ---
        # Use the new SQL that includes comparison data (prev_month/prev_year)
        # MATERIALIZED VIEW (mv_receive_daily) を使用してクエリパフォーマンス最適化
        # テーブル名は backend_shared.db.names の定数で置換済み（__init__で実行）

        try:
            result = self.db.execute(
                self._daily_comparisons_sql,
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
                # New SQL returns: ddate, iso_year, iso_week, iso_dow, is_business, segment,
                #                  ton, cum_ton, prev_month_ton, prev_year_ton,
                #                  prev_month_cum_ton, prev_year_cum_ton
                ddate = r[0]
                iso_year = r[1]
                iso_week = r[2]
                iso_dow = r[3]
                is_business = r[4]
                seg = r[5]  # 現状はNone相当の文字列NULL::text
                ton = float(r[6]) if r[6] is not None else 0.0
                cum = float(r[7]) if r[7] is not None else None
                prev_month_ton = float(r[8]) if r[8] is not None else None
                prev_year_ton = float(r[9]) if r[9] is not None else None
                prev_month_cum = float(r[10]) if r[10] is not None else None
                prev_year_cum = float(r[11]) if r[11] is not None else None

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
                        prev_month_ton=prev_month_ton,
                        prev_year_ton=prev_year_ton,
                        prev_month_cum_ton=prev_month_cum,
                        prev_year_cum_ton=prev_year_cum,
                    )
                )

            logger.info(
                "Fetched %d daily rows: %s to %s, segment=%s, cum_scope=%s",
                len(data),
                start,
                end,
                segment,
                cum_scope,
            )
            return data

        except Exception as e:
            logger.error(
                "Failed to fetch daily inbound: %s to %s, segment=%s, cum_scope=%s, error=%s",
                start,
                end,
                segment,
                cum_scope,
                e,
                exc_info=True,
            )
            raise

    def fetch_daily_simple(
        self,
        start: date_type,
        end: date_type,
        segment: Optional[str] = None,
    ) -> List[InboundDailyRow]:
        """
        案6: Simplified daily fetch without prev_month/prev_year comparisons.
        20-30% faster than fetch_daily(), suitable when comparisons are not needed.

        Args:
            start: Start date (inclusive)
            end: End date (inclusive)
            segment: Segment filter (currently not supported)

        Returns:
            List[InboundDailyRow] with day_ton, week_ton, and cumulative calculations.
            prev_month/prev_year fields will be None.
        """
        # --- Validation ---
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")
        delta_days = (end - start).days + 1
        if delta_days > 366:
            raise ValueError(f"Date range exceeds 366 days: {delta_days} days")

        if segment is not None:
            logger.warning(
                "segment filter is not supported on %s; ignoring segment=%r",
                fq(SCHEMA_MART, MV_RECEIVE_DAILY),
                segment,
            )

        # --- SQL with simple query (no comparisons) ---
        # backend_shared.db.names の定数で置換済み（__init__で実行）

        try:
            result = self.db.execute(
                self._daily_simple_sql,
                sql,
                {
                    "start": start,
                    "end": end,
                },
            )
            rows = result.fetchall()

            data: List[InboundDailyRow] = []
            for r in rows:
                # SQL returns: ddate, iso_year, iso_week, iso_dow, is_business,
                #              day_ton, week_ton, month_cumulative_ton, week_cumulative_ton
                ddate = r[0]
                iso_year = r[1]
                iso_week = r[2]
                iso_dow = r[3]
                is_business = r[4]
                day_ton = float(r[5]) if r[5] is not None else 0.0
                week_ton = float(r[6]) if r[6] is not None else None
                month_cum = float(r[7]) if r[7] is not None else None
                week_cum = float(r[8]) if r[8] is not None else None

                data.append(
                    InboundDailyRow(
                        ddate=ddate,
                        iso_year=iso_year,
                        iso_week=iso_week,
                        iso_dow=iso_dow,
                        is_business=is_business,
                        segment=None,  # Not supported in simple query
                        ton=day_ton,
                        cum_ton=month_cum,  # Treat as month cumulative
                        prev_month_ton=None,
                        prev_year_ton=None,
                        prev_month_cum_ton=None,
                        prev_year_cum_ton=None,
                    )
                )

            logger.info(
                "Fetched %d daily rows (simple): %s to %s, segment=%s",
                len(data),
                start,
                end,
                segment,
            )
            return data

        except Exception as e:
            logger.error(
                "Failed to fetch daily inbound (simple): %s to %s, segment=%s, error=%s",
                start,
                end,
                segment,
                e,
                exc_info=True,
            )
            raise
