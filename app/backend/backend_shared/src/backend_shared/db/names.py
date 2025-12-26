"""
PostgreSQL database object names (schema, table, view, materialized view)

This module provides constants for all database object names used in the application.
All SQL identifiers should reference these constants to:
- Prevent typos
- Enable IDE autocomplete
- Simplify refactoring (change in one place)
- Document database structure

⚠️ SECURITY WARNING:
Do NOT use these constants with user-provided input.
All parameters to fq() and schema_qualified() must be constants defined here.

Usage:
    from backend_shared.db.names import SCHEMA_MART, MV_RECEIVE_DAILY, fq

    sql = f"REFRESH MATERIALIZED VIEW {fq(SCHEMA_MART, MV_RECEIVE_DAILY)};"

Generated from DB reality check on 2025-12-11.
See: docs/backend/20251211_DB_REALITY_CHECK.md
"""

# ============================================================================
# Schema Names
# ============================================================================

SCHEMA_REF = "ref"  # Reference data (calendar, holidays, closures, masters)
SCHEMA_STG = "stg"  # Staging tables (ETL source data)
SCHEMA_MART = "mart"  # Data mart (aggregated views and materialized views)
SCHEMA_KPI = "kpi"  # KPI management tables
SCHEMA_RAW = "raw"  # Raw data from external systems
SCHEMA_LOG = "log"  # Logging tables

# ============================================================================
# ref schema - Reference Tables and Views
# ============================================================================

# Tables (マスタテーブル - SQL定義ファイルなし)
T_CALENDAR_DAY = "calendar_day"
T_CALENDAR_MONTH = "calendar_month"
T_CALENDAR_EXCEPTION = "calendar_exception"
T_CLOSURE_PERIODS = "closure_periods"
T_CLOSURE_MEMBERSHIP = "closure_membership"
T_HOLIDAY_JP = "holiday_jp"

# Views (SQL定義ファイルあり: migrations/alembic/sql/ref/*.sql)
V_CALENDAR_CLASSIFIED = "v_calendar_classified"
V_CLOSURE_DAYS = "v_closure_days"

# Views (SQL定義ファイルなし - 要調査)
V_CUSTOMER = "v_customer"
V_ITEM = "v_item"
V_SALES_REP = "v_sales_rep"

# ============================================================================
# stg schema - Staging Tables (ETL source)
# ============================================================================

# 将軍システム - 確定データ (final)
T_SHOGUN_FINAL_RECEIVE = "shogun_final_receive"
T_SHOGUN_FINAL_SHIPMENT = "shogun_final_shipment"
T_SHOGUN_FINAL_YARD = "shogun_final_yard"

# 将軍システム - 速報データ (flash)
T_SHOGUN_FLASH_RECEIVE = "shogun_flash_receive"
T_SHOGUN_FLASH_SHIPMENT = "shogun_flash_shipment"
T_SHOGUN_FLASH_YARD = "shogun_flash_yard"

# KINGシステム
T_RECEIVE_KING_FINAL = "receive_king_final"

# Active Views (is_deleted=false でフィルタリング)
# SQL定義ファイルなし - Alembic migration or 手動作成
V_ACTIVE_SHOGUN_FINAL_RECEIVE = "v_active_shogun_final_receive"
V_ACTIVE_SHOGUN_FINAL_SHIPMENT = "v_active_shogun_final_shipment"
V_ACTIVE_SHOGUN_FINAL_YARD = "v_active_shogun_final_yard"
V_ACTIVE_SHOGUN_FLASH_RECEIVE = "v_active_shogun_flash_receive"
V_ACTIVE_SHOGUN_FLASH_SHIPMENT = "v_active_shogun_flash_shipment"
V_ACTIVE_SHOGUN_FLASH_YARD = "v_active_shogun_flash_yard"

# KING Cleaning View
V_KING_RECEIVE_CLEAN = "v_king_receive_clean"

# Note: stg schema tables are managed by ETL processes
# SQL definition files do not exist for these tables

# ============================================================================
# mart schema - Data Mart (Views and Materialized Views)
# ============================================================================

# Materialized Views (auto-refreshed on CSV upload)
MV_RECEIVE_DAILY = "mv_receive_daily"  # 320KB, 1805 rows - auto-refresh
MV_TARGET_CARD_PER_DAY = "mv_target_card_per_day"  # 344KB, 2191 rows - auto-refresh

# Materialized Views (manual refresh only)
MV_INB5Y_WEEK_PROFILE_MIN = "mv_inb5y_week_profile_min"  # 32KB, 53 rows
MV_INB_AVG5Y_DAY_BIZ = "mv_inb_avg5y_day_biz"  # 64KB, 312 rows
MV_INB_AVG5Y_WEEKSUM_BIZ = "mv_inb_avg5y_weeksum_biz"  # 40KB, 53 rows
MV_INB_AVG5Y_DAY_SCOPE = "mv_inb_avg5y_day_scope"  # 184KB, 679 rows

# Views (computed on-demand - SQL定義ファイルあり)
V_RECEIVE_DAILY = "v_receive_daily"
V_RECEIVE_WEEKLY = "v_receive_weekly"
V_RECEIVE_MONTHLY = "v_receive_monthly"
V_DAILY_TARGET_WITH_CALENDAR = "v_daily_target_with_calendar"
V_RESERVE_DAILY_FOR_FORECAST = "v_reserve_daily_for_forecast"  # 予測用予約データ

# Views (SQL定義ファイルなし)
V_CUSTOMER_SALES_DAILY = "v_customer_sales_daily"
V_SALES_TREE_DAILY = "v_sales_tree_daily"
V_SALES_TREE_DETAIL_BASE = "v_sales_tree_detail_base"

# Tables
T_DAILY_TARGET_PLAN = "daily_target_plan"
T_INB_PROFILE_SMOOTH_TEST = "inb_profile_smooth_test"  # 実験用テーブル

# ============================================================================
# kpi schema - KPI Management
# ============================================================================

T_MONTHLY_TARGETS = "monthly_targets"

# ============================================================================
# log schema - Logging Tables
# ============================================================================

T_UPLOAD_FILE = "upload_file"  # CSV upload tracking

# ============================================================================
# Helper Functions
# ============================================================================


def fq(schema: str, name: str) -> str:
    """
    Return fully-qualified PostgreSQL identifier: "schema"."name"

    Args:
        schema: Schema name (use SCHEMA_* constants)
        name: Object name (use T_*, V_*, MV_* constants)

    Returns:
        Quoted identifier: "schema"."name"

    Example:
        >>> fq(SCHEMA_MART, MV_RECEIVE_DAILY)
        '"mart"."mv_receive_daily"'

    Security:
        - This function is safe for SQL construction ONLY with constants
        - Do NOT use with user-provided strings (SQL injection risk)
        - All inputs MUST be constants defined in this module
    """
    return f'"{schema}"."{name}"'


def schema_qualified(schema: str, name: str) -> str:
    """
    Return schema-qualified identifier without quotes: schema.name

    Use this for contexts where quotes are not needed (e.g., psycopg3 Identifier)

    Args:
        schema: Schema name (use SCHEMA_* constants)
        name: Object name (use T_*, V_*, MV_* constants)

    Returns:
        Unquoted identifier: schema.name

    Example:
        >>> schema_qualified(SCHEMA_MART, MV_RECEIVE_DAILY)
        'mart.mv_receive_daily'
    """
    return f"{schema}.{name}"


# ============================================================================
# Object Collections (for batch operations)
# ============================================================================

# All materialized views in mart schema (for refresh operations)
ALL_MART_MVS = [
    MV_RECEIVE_DAILY,
    MV_TARGET_CARD_PER_DAY,
    MV_INB5Y_WEEK_PROFILE_MIN,
    MV_INB_AVG5Y_DAY_BIZ,
    MV_INB_AVG5Y_WEEKSUM_BIZ,
    MV_INB_AVG5Y_DAY_SCOPE,
]

# Auto-refreshed MVs (configured in MaterializedViewRefresher)
AUTO_REFRESH_MVS = [
    MV_RECEIVE_DAILY,
    MV_TARGET_CARD_PER_DAY,
]

# 5-year average MVs (statistical analysis)
FIVE_YEAR_AVG_MVS = [
    MV_INB5Y_WEEK_PROFILE_MIN,
    MV_INB_AVG5Y_DAY_BIZ,
    MV_INB_AVG5Y_WEEKSUM_BIZ,
    MV_INB_AVG5Y_DAY_SCOPE,
]

# 将軍システム全テーブル (shogun tables)
SHOGUN_FINAL_TABLES = [
    T_SHOGUN_FINAL_RECEIVE,
    T_SHOGUN_FINAL_SHIPMENT,
    T_SHOGUN_FINAL_YARD,
]

SHOGUN_FLASH_TABLES = [
    T_SHOGUN_FLASH_RECEIVE,
    T_SHOGUN_FLASH_SHIPMENT,
    T_SHOGUN_FLASH_YARD,
]

# Active views (is_deleted=false filtering)
SHOGUN_ACTIVE_VIEWS = [
    V_ACTIVE_SHOGUN_FINAL_RECEIVE,
    V_ACTIVE_SHOGUN_FINAL_SHIPMENT,
    V_ACTIVE_SHOGUN_FINAL_YARD,
    V_ACTIVE_SHOGUN_FLASH_RECEIVE,
    V_ACTIVE_SHOGUN_FLASH_SHIPMENT,
    V_ACTIVE_SHOGUN_FLASH_YARD,
]
