"""
Dashboard target repository: fetch monthly/weekly/daily targets and actuals.
Optimized with single-query anchor resolution and NULL masking.
"""
from datetime import date as date_type, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

from app.infra.db.db import get_engine

logger = logging.getLogger(__name__)


class DashboardTargetRepository:
    """Repository for retrieving target and actual metrics from mart.v_target_card_per_day."""

    def __init__(self, db: Session):
        self.db = db
        self._engine = get_engine()

    def get_by_date_optimized(self, target_date: date_type, mode: str = "daily") -> Optional[Dict[str, Any]]:
        """
        Optimized single-query fetch with anchor resolution and NULL masking.
        Now also calculates cumulative and total targets for achievement modes.
        
        Anchor logic (all in one SQL query):
        - Current month: Use today (or month_end if today > month_end)
        - Past month: Use month_end
        - Future month: Use first business day (or month_start if none exists)
        
        NULL masking (mode='monthly' and not current month):
        - day_target_ton, week_target_ton, day_actual_ton_prev, week_actual_ton → NULL
        
        New fields for achievement rate calculation:
        - month_target_to_date_ton: SUM(day_target_ton) from month_start to yesterday
        - month_target_total_ton: MAX(month_target_ton) for the entire month
        - week_target_to_date_ton: SUM(day_target_ton) from week_start to yesterday
        - week_target_total_ton: MAX(week_target_ton) for the entire week
        - month_actual_to_date_ton: SUM(receive_net_ton) from month_start to yesterday
        - week_actual_to_date_ton: SUM(receive_net_ton) from week_start to yesterday
        
        Args:
            target_date: Requested date (typically first day of month)
            mode: 'daily' or 'monthly'
            
        Returns:
            Dict with all target/actual fields including cumulative and total targets, or None if no data found
        """
        try:
            query = text("""
WITH today AS (
  SELECT CURRENT_DATE::date AS today
),
bounds AS (
  SELECT
    date_trunc('month', CAST(:req AS DATE))::date AS month_start,
    (date_trunc('month', CAST(:req AS DATE)) + INTERVAL '1 month - 1 day')::date AS month_end
),
anchor AS (
  SELECT CASE
    -- Current month: use today (or month_end if today exceeds it)
    WHEN date_trunc('month', CAST(:req AS DATE)) = date_trunc('month', (SELECT today FROM today))
      THEN LEAST((SELECT today FROM today), (SELECT month_end FROM bounds))
    -- Past month: use month_end
    WHEN date_trunc('month', CAST(:req AS DATE)) < date_trunc('month', (SELECT today FROM today))
      THEN (SELECT month_end FROM bounds)
    -- Future month: use first business day (or month_start if none)
    ELSE COALESCE(
      (SELECT MIN(v.ddate)::date
       FROM mart.v_target_card_per_day v
       WHERE v.ddate BETWEEN (SELECT month_start FROM bounds) AND (SELECT month_end FROM bounds)
         AND v.is_business = true),
      (SELECT month_start FROM bounds)
    )
  END AS ddate
),
base AS (
  SELECT
    v.ddate,
    v.day_target_ton, v.week_target_ton, v.month_target_ton,
    v.day_actual_ton_prev, v.week_actual_ton, v.month_actual_ton,
    v.iso_year, v.iso_week, v.iso_dow, v.day_type, v.is_business
  FROM mart.v_target_card_per_day v
  JOIN anchor a ON v.ddate = a.ddate
  LIMIT 1
),
-- アンカー日の前日を計算（選択月内に限定）
anchor_yesterday AS (
  SELECT 
    CASE
      -- アンカー日が月初の場合は月初を使用（前日がないため）
      WHEN (SELECT ddate FROM anchor) = (SELECT month_start FROM bounds)
        THEN (SELECT month_start FROM bounds)
      -- それ以外はアンカー日の前日
      ELSE ((SELECT ddate FROM anchor) - INTERVAL '1 day')::date
    END AS anchor_yesterday_date
),
-- Calculate month cumulative target (sum of day_target_ton from month_start to anchor_yesterday)
-- 選択月内のみを対象とする
month_target_to_date AS (
  SELECT COALESCE(SUM(v.day_target_ton), 0)::numeric AS month_target_to_date_ton
  FROM mart.v_target_card_per_day v
  WHERE v.ddate BETWEEN (SELECT month_start FROM bounds) AND (SELECT anchor_yesterday_date FROM anchor_yesterday)
),
-- Calculate month total target (max of month_target_ton for the entire month)
month_target_total AS (
  SELECT COALESCE(MAX(v.month_target_ton), 0)::numeric AS month_target_total_ton
  FROM mart.v_target_card_per_day v
  WHERE v.ddate BETWEEN (SELECT month_start FROM bounds) AND (SELECT month_end FROM bounds)
),
-- Calculate week cumulative target (sum of day_target_ton from week_start to anchor_yesterday, same iso_year/iso_week)
-- 選択月内かつ同一週のみを対象とする
week_target_to_date AS (
  SELECT COALESCE(SUM(v.day_target_ton), 0)::numeric AS week_target_to_date_ton
  FROM mart.v_target_card_per_day v, base b
  WHERE v.iso_year = b.iso_year
    AND v.iso_week = b.iso_week
    AND v.ddate >= (SELECT month_start FROM bounds)
    AND v.ddate <= (SELECT anchor_yesterday_date FROM anchor_yesterday)
),
-- Calculate week total target (max of week_target_ton for the entire week)
-- 週全体だが選択月内のみ
week_target_total AS (
  SELECT COALESCE(MAX(v.week_target_ton), 0)::numeric AS week_target_total_ton
  FROM mart.v_target_card_per_day v, base b
  WHERE v.iso_year = b.iso_year
    AND v.iso_week = b.iso_week
    AND v.ddate >= (SELECT month_start FROM bounds)
    AND v.ddate <= (SELECT month_end FROM bounds)
),
-- Calculate month cumulative actual (sum of receive_net_ton from month_start to anchor_yesterday)
-- 選択月内のみを対象とする
month_actual_to_date AS (
  SELECT COALESCE(SUM(r.receive_net_ton), 0)::numeric AS month_actual_to_date_ton
  FROM mart.v_receive_daily r
  WHERE r.ddate BETWEEN (SELECT month_start FROM bounds) AND (SELECT anchor_yesterday_date FROM anchor_yesterday)
),
-- Calculate week cumulative actual (sum of receive_net_ton from week_start to anchor_yesterday, same iso_year/iso_week)
-- 選択月内かつ同一週のみを対象とする
week_actual_to_date AS (
  SELECT COALESCE(SUM(r.receive_net_ton), 0)::numeric AS week_actual_to_date_ton
  FROM mart.v_receive_daily r, base b
  WHERE r.iso_year = b.iso_year
    AND r.iso_week = b.iso_week
    AND r.ddate >= (SELECT month_start FROM bounds)
    AND r.ddate <= (SELECT anchor_yesterday_date FROM anchor_yesterday)
)
SELECT
  b.ddate,
  -- Apply NULL masking for day/week fields when mode=monthly and not current month
  CASE
    WHEN :mode = 'monthly'
     AND date_trunc('month', CAST(:req AS DATE)) <> date_trunc('month', (SELECT today FROM today))
    THEN NULL ELSE b.day_target_ton END AS day_target_ton,
  CASE
    WHEN :mode = 'monthly'
     AND date_trunc('month', CAST(:req AS DATE)) <> date_trunc('month', (SELECT today FROM today))
    THEN NULL ELSE b.week_target_ton END AS week_target_ton,
  b.month_target_ton,
  CASE
    WHEN :mode = 'monthly'
     AND date_trunc('month', CAST(:req AS DATE)) <> date_trunc('month', (SELECT today FROM today))
    THEN NULL ELSE b.day_actual_ton_prev END AS day_actual_ton_prev,
  CASE
    WHEN :mode = 'monthly'
     AND date_trunc('month', CAST(:req AS DATE)) <> date_trunc('month', (SELECT today FROM today))
    THEN NULL ELSE b.week_actual_ton END AS week_actual_ton,
  b.month_actual_ton,
  b.iso_year, b.iso_week, b.iso_dow, b.day_type, b.is_business,
  -- New cumulative and total target fields
  (SELECT month_target_to_date_ton FROM month_target_to_date) AS month_target_to_date_ton,
  (SELECT month_target_total_ton FROM month_target_total) AS month_target_total_ton,
  (SELECT week_target_to_date_ton FROM week_target_to_date) AS week_target_to_date_ton,
  (SELECT week_target_total_ton FROM week_target_total) AS week_target_total_ton,
  (SELECT month_actual_to_date_ton FROM month_actual_to_date) AS month_actual_to_date_ton,
  (SELECT week_actual_to_date_ton FROM week_actual_to_date) AS week_actual_to_date_ton
FROM base b;
            """)
            
            logger.info(f"Fetching optimized target card data for date={target_date}, mode={mode}")
            
            with self._engine.begin() as conn:
                result = conn.execute(query, {"req": target_date, "mode": mode}).mappings().first()
            
            if not result:
                logger.warning(f"No data found for date={target_date}, mode={mode}")
                return None
            
            logger.info(f"Successfully fetched optimized target card data for {target_date}")
            return {
                "ddate": result["ddate"],
                "month_target_ton": float(result["month_target_ton"]) if result["month_target_ton"] is not None else None,
                "week_target_ton": float(result["week_target_ton"]) if result["week_target_ton"] is not None else None,
                "day_target_ton": float(result["day_target_ton"]) if result["day_target_ton"] is not None else None,
                "month_actual_ton": float(result["month_actual_ton"]) if result["month_actual_ton"] is not None else None,
                "week_actual_ton": float(result["week_actual_ton"]) if result["week_actual_ton"] is not None else None,
                "day_actual_ton_prev": float(result["day_actual_ton_prev"]) if result["day_actual_ton_prev"] is not None else None,
                "iso_year": result["iso_year"],
                "iso_week": result["iso_week"],
                "iso_dow": result["iso_dow"],
                "day_type": result["day_type"],
                "is_business": result["is_business"],
                # New cumulative and total target/actual fields
                "month_target_to_date_ton": float(result["month_target_to_date_ton"]) if result["month_target_to_date_ton"] is not None else None,
                "month_target_total_ton": float(result["month_target_total_ton"]) if result["month_target_total_ton"] is not None else None,
                "week_target_to_date_ton": float(result["week_target_to_date_ton"]) if result["week_target_to_date_ton"] is not None else None,
                "week_target_total_ton": float(result["week_target_total_ton"]) if result["week_target_total_ton"] is not None else None,
                "month_actual_to_date_ton": float(result["month_actual_to_date_ton"]) if result["month_actual_to_date_ton"] is not None else None,
                "week_actual_to_date_ton": float(result["week_actual_to_date_ton"]) if result["week_actual_to_date_ton"] is not None else None,
            }
        except Exception as e:
            logger.error(f"Error fetching optimized target card data for {target_date}: {str(e)}", exc_info=True)
            raise

    def get_by_date(self, target_date: date_type) -> Optional[Dict[str, Any]]:
        """
        Get target and actual metrics for a specific date.
        
        Returns:
            Dict with all columns from mart.v_target_card_per_day including:
                - month_target_ton, week_target_ton, day_target_ton
                - month_actual_ton, week_actual_ton, day_actual_ton_prev
                - iso_year, iso_week, iso_dow
                - day_type, is_business
                - ddate
        """
        try:
            query = text("""
                SELECT 
                    ddate,
                    month_target_ton,
                    week_target_ton,
                    day_target_ton,
                    month_actual_ton,
                    week_actual_ton,
                    day_actual_ton_prev,
                    iso_year,
                    iso_week,
                    iso_dow,
                    day_type,
                    is_business
                FROM mart.v_target_card_per_day
                WHERE ddate = CAST(:target_date AS DATE)
                LIMIT 1
            """)
            
            logger.info(f"Fetching target card data for date: {target_date}")
            result = self.db.execute(query, {"target_date": target_date}).fetchone()
            
            if not result:
                logger.warning(f"No data found in mart.v_target_card_per_day for {target_date}")
                return None
            
            logger.info(f"Successfully fetched target card data for {target_date}")
            return {
                "ddate": result[0],
                "month_target_ton": float(result[1]) if result[1] is not None else None,
                "week_target_ton": float(result[2]) if result[2] is not None else None,
                "day_target_ton": float(result[3]) if result[3] is not None else None,
                "month_actual_ton": float(result[4]) if result[4] is not None else None,
                "week_actual_ton": float(result[5]) if result[5] is not None else None,
                "day_actual_ton_prev": float(result[6]) if result[6] is not None else None,
                "iso_year": result[7],
                "iso_week": result[8],
                "iso_dow": result[9],
                "day_type": result[10],
                "is_business": result[11],
            }
        except Exception as e:
            logger.error(f"Error fetching target card data for {target_date}: {str(e)}", exc_info=True)
            raise

    def get_first_business_in_month(self, month_start: date_type, month_end: date_type) -> Optional[date_type]:
        """
        Get the first business day in the specified month range.
        
        Args:
            month_start: First day of the month
            month_end: Last day of the month
            
        Returns:
            The first business day in the month, or None if not found
        """
        try:
            query = text("""
                SELECT ddate
                FROM mart.v_target_card_per_day
                WHERE ddate BETWEEN CAST(:month_start AS DATE) AND CAST(:month_end AS DATE)
                  AND is_business = true
                ORDER BY ddate ASC
                LIMIT 1
            """)
            
            result = self.db.execute(query, {"month_start": month_start, "month_end": month_end}).fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting first business day for {month_start} to {month_end}: {str(e)}", exc_info=True)
            raise

    def get_target_card_metrics(self, target_date: date_type) -> Optional[Dict[str, Any]]:
        """
        Get target and actual metrics from mart.v_target_card_per_day.
        
        For the specified date's month, retrieves the LAST day's record of that month
        to get cumulative actuals (month_actual_ton, week_actual_ton) and targets.
        
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
            # まずビューの存在を確認
            check_view = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'mart' 
                      AND table_name = 'v_target_card_per_day'
                )
            """)
            view_exists = self.db.execute(check_view).scalar()
            
            if not view_exists:
                logger.error("View mart.v_target_card_per_day does not exist!")
                raise ValueError("View mart.v_target_card_per_day does not exist. Please create the view first.")
            
            query = text("""
                SELECT 
                    month_target_ton,
                    week_target_ton,
                    day_target_ton,
                    month_actual_ton,
                    week_actual_ton,
                    day_actual_ton_prev,
                    ddate
                FROM mart.v_target_card_per_day
                WHERE date_trunc('month', ddate) = date_trunc('month', CAST(:target_date AS DATE))
                ORDER BY ddate DESC
                LIMIT 1
            """)
            
            logger.info(f"Fetching target card metrics for date: {target_date}")
            result = self.db.execute(query, {"target_date": target_date}).fetchone()
            
            if not result:
                logger.warning(f"No data found in mart.v_target_card_per_day for month containing {target_date}")
                return None
            
            logger.info(f"Successfully fetched target card metrics for {target_date}")
            return {
                "month_target_ton": float(result[0]) if result[0] is not None else None,
                "week_target_ton": float(result[1]) if result[1] is not None else None,
                "day_target_ton": float(result[2]) if result[2] is not None else None,
                "month_actual_ton": float(result[3]) if result[3] is not None else None,
                "week_actual_ton": float(result[4]) if result[4] is not None else None,
                "day_actual_ton_prev": float(result[5]) if result[5] is not None else None,
            }
        except Exception as e:
            logger.error(f"Error fetching target card metrics for {target_date}: {str(e)}", exc_info=True)
            raise

