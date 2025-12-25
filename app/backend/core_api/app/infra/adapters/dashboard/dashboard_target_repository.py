"""
Dashboard target repository: fetch monthly/weekly/daily targets and actuals.
Optimized with single-query anchor resolution and NULL masking.
"""

from datetime import date as date_type
from typing import Any

from app.infra.db.db import get_engine
from app.infra.db.sql_loader import load_sql
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.db.names import MV_TARGET_CARD_PER_DAY, SCHEMA_MART, fq
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = get_module_logger(__name__)


class DashboardTargetRepository:
    """Repository for retrieving target and actual metrics from mart.mv_target_card_per_day (Materialized View).

    Performance Note:
    - Switched from VIEW to MATERIALIZED VIEW for faster response times
    - MV is refreshed daily via MaterializedViewRefresher on CSV upload
    - Uses backend_shared.db.names constants for DB object references
    """

    def __init__(self, db: Session):
        self.db = db
        self._engine = get_engine()
        # Pre-load and compile SQL queries for performance
        self._get_by_date_optimized_sql = text(
            load_sql("dashboard/dashboard_target_repo__get_by_date_optimized.sql")
        )
        # Load other SQL queries with schema/table name substitution
        template_get_by_date = load_sql(
            "dashboard/dashboard_target_repo__get_by_date.sql"
        )
        self._get_by_date_sql = text(
            template_get_by_date.format(
                schema_mart=SCHEMA_MART,
                mv_target_card_per_day=MV_TARGET_CARD_PER_DAY,
            )
        )
        template_first_business = load_sql(
            "dashboard/dashboard_target_repo__get_first_business_day.sql"
        )
        self._get_first_business_day_sql = text(
            template_first_business.format(
                schema_mart=SCHEMA_MART,
                mv_target_card_per_day=MV_TARGET_CARD_PER_DAY,
            )
        )
        template_metrics = load_sql(
            "dashboard/dashboard_target_repo__get_target_card_metrics.sql"
        )
        self._get_target_card_metrics_sql = text(
            template_metrics.format(
                schema_mart=SCHEMA_MART,
                mv_target_card_per_day=MV_TARGET_CARD_PER_DAY,
            )
        )

    def get_by_date_optimized(
        self, target_date: date_type, mode: str = "daily"
    ) -> dict[str, Any] | None:
        """
        最適化されたターゲットデータ取得（アンカー解決 + NULLマスキング）

        機能:
          1. アンカー日付の自動解決（全てSQLクエリ内で完結）
             - 当月: 今日を使用（今日 > 月末の場合は月末）
             - 過去月: 月末を使用
             - 未来月: 最初の営業日を使用（存在しない場合は月初）
          2. NULLマスキング（mode='monthly' かつ当月以外）
             - day_target_ton, week_target_ton, day_actual_ton_prev, week_actual_ton → NULL
             - フロントエンドでは「—」で表示
          3. 達成率計算用の累計・合計ターゲット
             - month_target_to_date_ton: 月初～昨日までのday_target_tonの累計
             - month_target_total_ton: 月全体のMAX(month_target_ton)
             - week_target_to_date_ton: 週初～昨日までのday_target_tonの累計
             - week_target_total_ton: 週全体のMAX(week_target_ton)
             - month_actual_to_date_ton: 月初～昨日までのreceive_net_tonの累計
             - week_actual_to_date_ton: 週初～昨日までのreceive_net_tonの累計

        パフォーマンス最適化（2025-11-17）:
          - VIEW → MATERIALIZED VIEW（mart.mv_target_card_per_day）に切り替え
          - 狙い: 複雑なJOIN/集計をMV側で事前計算し、レスポンスタイム短縮
          - 前提: MVは日次で REFRESH CONCURRENTLY（make refresh-mv）
          - ロールバック: mart.v_target_card_per_day（VIEW）に戻すことも可能

        Args:
            target_date: リクエスト日付（通常は月初）
            mode: 'daily' or 'monthly'

        Returns:
            Dict: ターゲット/実績フィールド（累計・合計を含む）、データがない場合はNone
        """
        try:
            # クエリ最適化: VIEW → MV 参照に変更（2025-11-17）
            # 狙い: 複雑なJOIN/集計をMV側で事前計算し、レスポンスタイム短縮
            # 注意: MV は日次で REFRESH CONCURRENTLY される前提（make refresh-mv）
            # SQL is loaded from external file for better maintainability

            logger.info(
                "最適化target cardデータ取得開始",
                extra=create_log_context(
                    operation="get_by_date_optimized", date=str(target_date), mode=mode
                ),
            )

            with self._engine.begin() as conn:
                result = (
                    conn.execute(
                        self._get_by_date_optimized_sql,
                        {"req": target_date, "mode": mode},
                    )
                    .mappings()
                    .first()
                )

            if not result:
                logger.warning(
                    "target cardデータ未検出",
                    extra=create_log_context(
                        operation="get_by_date_optimized",
                        date=str(target_date),
                        mode=mode,
                    ),
                )
                return None

            logger.info(
                "target cardデータ取得成功",
                extra=create_log_context(
                    operation="get_by_date_optimized", date=str(target_date)
                ),
            )
            return {
                "ddate": result["ddate"],
                "month_target_ton": (
                    float(result["month_target_ton"])
                    if result["month_target_ton"] is not None
                    else None
                ),
                "week_target_ton": (
                    float(result["week_target_ton"])
                    if result["week_target_ton"] is not None
                    else None
                ),
                "day_target_ton": (
                    float(result["day_target_ton"])
                    if result["day_target_ton"] is not None
                    else None
                ),
                "month_actual_ton": (
                    float(result["month_actual_ton"])
                    if result["month_actual_ton"] is not None
                    else None
                ),
                "week_actual_ton": (
                    float(result["week_actual_ton"])
                    if result["week_actual_ton"] is not None
                    else None
                ),
                "day_actual_ton_prev": (
                    float(result["day_actual_ton_prev"])
                    if result["day_actual_ton_prev"] is not None
                    else None
                ),
                "iso_year": result["iso_year"],
                "iso_week": result["iso_week"],
                "iso_dow": result["iso_dow"],
                "day_type": result["day_type"],
                "is_business": result["is_business"],
                # New cumulative and total target/actual fields
                "month_target_to_date_ton": (
                    float(result["month_target_to_date_ton"])
                    if result["month_target_to_date_ton"] is not None
                    else None
                ),
                "month_target_total_ton": (
                    float(result["month_target_total_ton"])
                    if result["month_target_total_ton"] is not None
                    else None
                ),
                "week_target_to_date_ton": (
                    float(result["week_target_to_date_ton"])
                    if result["week_target_to_date_ton"] is not None
                    else None
                ),
                "week_target_total_ton": (
                    float(result["week_target_total_ton"])
                    if result["week_target_total_ton"] is not None
                    else None
                ),
                "month_actual_to_date_ton": (
                    float(result["month_actual_to_date_ton"])
                    if result["month_actual_to_date_ton"] is not None
                    else None
                ),
                "week_actual_to_date_ton": (
                    float(result["week_actual_to_date_ton"])
                    if result["week_actual_to_date_ton"] is not None
                    else None
                ),
            }
        except Exception as e:
            logger.error(
                "target cardデータ取得エラー",
                extra=create_log_context(
                    operation="get_by_date_optimized",
                    date=str(target_date),
                    error=str(e),
                ),
                exc_info=True,
            )
            raise

    def get_by_date(self, target_date: date_type) -> dict[str, Any] | None:
        """
        Get target and actual metrics for a specific date.

        Returns:
            Dict with all columns from mart.mv_target_card_per_day including:
                - month_target_ton, week_target_ton, day_target_ton
                - month_actual_ton, week_actual_ton, day_actual_ton_prev
                - iso_year, iso_week, iso_dow
                - day_type, is_business
                - ddate
        """
        try:
            # MATERIALIZED VIEWを使用して高速クエリ（SQL は外部ファイルから読み込み）
            logger.info(
                "target cardデータ取得開始(get_by_date)",
                extra=create_log_context(
                    operation="get_by_date", date=str(target_date)
                ),
            )
            result = self.db.execute(
                self._get_by_date_sql, {"target_date": target_date}
            ).fetchone()

            if not result:
                logger.warning(
                    "mv_target_card_per_dayにデータ未検出",
                    extra=create_log_context(
                        operation="get_by_date", date=str(target_date)
                    ),
                )
                return None

            logger.info(
                "target cardデータ取得成功(get_by_date)",
                extra=create_log_context(
                    operation="get_by_date", date=str(target_date)
                ),
            )
            return {
                "ddate": result[0],
                "month_target_ton": float(result[1]) if result[1] is not None else None,
                "week_target_ton": float(result[2]) if result[2] is not None else None,
                "day_target_ton": float(result[3]) if result[3] is not None else None,
                "month_actual_ton": float(result[4]) if result[4] is not None else None,
                "week_actual_ton": float(result[5]) if result[5] is not None else None,
                "day_actual_ton_prev": (
                    float(result[6]) if result[6] is not None else None
                ),
                "iso_year": result[7],
                "iso_week": result[8],
                "iso_dow": result[9],
                "day_type": result[10],
                "is_business": result[11],
            }
        except Exception as e:
            logger.error(
                "target cardデータ取得エラー(get_by_date)",
                extra=create_log_context(
                    operation="get_by_date", date=str(target_date), error=str(e)
                ),
                exc_info=True,
            )
            raise

    def get_first_business_in_month(
        self, month_start: date_type, month_end: date_type
    ) -> date_type | None:
        """
        Get the first business day in the specified month range.

        Args:
            month_start: First day of the month
            month_end: Last day of the month

        Returns:
            The first business day in the month, or None if not found
        """
        try:
            # MATERIALIZED VIEWを使用（SQL は外部ファイルから読み込み）
            result = self.db.execute(
                self._get_first_business_day_sql,
                {"month_start": month_start, "month_end": month_end},
            ).fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(
                "最初の営業日取得エラー",
                extra=create_log_context(
                    operation="get_first_business_day_of_month",
                    month_start=str(month_start),
                    month_end=str(month_end),
                    error=str(e),
                ),
                exc_info=True,
            )
            raise

    def get_target_card_metrics(self, target_date: date_type) -> dict[str, Any] | None:
        """
        Get target and actual metrics from mart.mv_target_card_per_day (Materialized View).

        For the specified date's month, retrieves the LAST day's record of that month
        to get cumulative actuals (month_actual_ton, week_actual_ton) and targets.

        Performance Note:
        - Using MATERIALIZED VIEW for faster queries (pre-aggregated data)
        - MV refreshed daily via `make refresh-mv`

        Returns:
            Dict with keys:
                - month_target_ton
                - week_target_ton
                - day_target_ton
                - month_actual_ton
                - week_actual_ton
                - day_actual_ton_prev
        """
        try:
            # ★ MVの存在確認に変更（VIEW→MV）
            check_view = text(
                """
                SELECT EXISTS (
                    SELECT FROM pg_matviews
                    WHERE schemaname = 'mart'
                      AND matviewname = 'mv_target_card_per_day'
                )
            """
            )
            view_exists = self.db.execute(check_view).scalar()

            if not view_exists:
                logger.error(
                    f"Materialized View {fq(SCHEMA_MART, MV_TARGET_CARD_PER_DAY)} does not exist!"
                )
                raise ValueError(
                    f"Materialized View {fq(SCHEMA_MART, MV_TARGET_CARD_PER_DAY)} does not exist. Please run migration first."
                )

            # MATERIALIZED VIEWを使用（SQL は外部ファイルから読み込み）
            logger.info(
                "target card metrics取得開始",
                extra=create_log_context(
                    operation="get_target_card_metrics", date=str(target_date)
                ),
            )
            result = self.db.execute(
                self._get_target_card_metrics_sql, {"target_date": target_date}
            ).fetchone()

            if not result:
                logger.warning(
                    "指定月のmv_target_card_per_dayデータ未検出",
                    extra=create_log_context(
                        operation="get_target_card_metrics", date=str(target_date)
                    ),
                )
                return None

            logger.info(
                "target card metrics取得成功",
                extra=create_log_context(
                    operation="get_target_card_metrics", date=str(target_date)
                ),
            )
            return {
                "month_target_ton": float(result[0]) if result[0] is not None else None,
                "week_target_ton": float(result[1]) if result[1] is not None else None,
                "day_target_ton": float(result[2]) if result[2] is not None else None,
                "month_actual_ton": float(result[3]) if result[3] is not None else None,
                "week_actual_ton": float(result[4]) if result[4] is not None else None,
                "day_actual_ton_prev": (
                    float(result[5]) if result[5] is not None else None
                ),
            }
        except Exception as e:
            logger.error(
                "target card metrics取得エラー",
                extra=create_log_context(
                    operation="get_target_card_metrics",
                    date=str(target_date),
                    error=str(e),
                ),
                exc_info=True,
            )
            raise
