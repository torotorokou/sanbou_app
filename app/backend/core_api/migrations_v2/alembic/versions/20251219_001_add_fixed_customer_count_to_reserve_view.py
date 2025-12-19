"""add fixed customer count to reserve view

Revision ID: 20251219_001
Revises: 20251216_004
Create Date: 2025-12-19

固定客数（企業数）をv_reserve_daily_for_forecastビューに追加
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251219_001'
down_revision = '20251216_004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """ビューに固定客数（企業数）を追加"""
    
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_reserve_daily_for_forecast AS
        WITH customer_agg AS (
            -- 顧客別データを日次集計
            SELECT
                reserve_date AS date,
                SUM(planned_trucks) AS reserve_trucks,
                SUM(CASE WHEN is_fixed_customer THEN planned_trucks ELSE 0 END) AS reserve_fixed_trucks,
                COUNT(*) FILTER (WHERE is_fixed_customer = true) AS reserve_fixed_customer_count,
                'customer_agg' AS source
            FROM stg.reserve_customer_daily
            GROUP BY reserve_date
        ),
        manual_data AS (
            -- manual入力データ（論理削除を除外）
            -- 注意: manual入力では固定客数は不明なため、固定客台数から推定（1社=1台と仮定）
            SELECT
                reserve_date AS date,
                total_trucks AS reserve_trucks,
                fixed_trucks AS reserve_fixed_trucks,
                fixed_trucks AS reserve_fixed_customer_count,  -- 台数=企業数と仮定
                'manual' AS source
            FROM stg.reserve_daily_manual
            WHERE deleted_at IS NULL  -- 論理削除を除外
        ),
        combined AS (
            -- manual優先でデータを統合
            SELECT
                COALESCE(m.date, c.date) AS date,
                COALESCE(m.reserve_trucks, c.reserve_trucks, 0) AS reserve_trucks,
                COALESCE(m.reserve_fixed_trucks, c.reserve_fixed_trucks, 0) AS reserve_fixed_trucks,
                COALESCE(m.reserve_fixed_customer_count, c.reserve_fixed_customer_count, 0) AS reserve_fixed_customer_count,
                COALESCE(m.source, c.source) AS source
            FROM manual_data m
            FULL OUTER JOIN customer_agg c ON m.date = c.date
            WHERE COALESCE(m.date, c.date) IS NOT NULL
        )
        SELECT
            date,
            reserve_trucks,
            reserve_fixed_trucks,
            reserve_fixed_customer_count,
            CASE 
                WHEN reserve_trucks > 0 THEN 
                    ROUND(reserve_fixed_trucks::numeric / reserve_trucks::numeric, 4)
                ELSE 0
            END AS reserve_fixed_ratio,
            source
        FROM combined
        ORDER BY date;
    """)
    
    # カラムコメント追加
    op.execute("""
        COMMENT ON COLUMN mart.v_reserve_daily_for_forecast.reserve_fixed_customer_count IS 
        '固定客数（固定客の企業数）';
    """)


def downgrade() -> None:
    """ビューを以前の定義に戻す"""
    
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_reserve_daily_for_forecast AS
        WITH customer_agg AS (
            -- 顧客別データを日次集計
            SELECT
                reserve_date AS date,
                SUM(planned_trucks) AS reserve_trucks,
                SUM(CASE WHEN is_fixed_customer THEN planned_trucks ELSE 0 END) AS reserve_fixed_trucks,
                'customer_agg' AS source
            FROM stg.reserve_customer_daily
            GROUP BY reserve_date
        ),
        manual_data AS (
            -- manual入力データ（論理削除を除外）
            SELECT
                reserve_date AS date,
                total_trucks AS reserve_trucks,
                fixed_trucks AS reserve_fixed_trucks,
                'manual' AS source
            FROM stg.reserve_daily_manual
            WHERE deleted_at IS NULL  -- 論理削除を除外
        ),
        combined AS (
            -- manual優先でデータを統合
            SELECT
                COALESCE(m.date, c.date) AS date,
                COALESCE(m.reserve_trucks, c.reserve_trucks, 0) AS reserve_trucks,
                COALESCE(m.reserve_fixed_trucks, c.reserve_fixed_trucks, 0) AS reserve_fixed_trucks,
                COALESCE(m.source, c.source) AS source
            FROM manual_data m
            FULL OUTER JOIN customer_agg c ON m.date = c.date
            WHERE COALESCE(m.date, c.date) IS NOT NULL
        )
        SELECT
            date,
            reserve_trucks,
            reserve_fixed_trucks,
            CASE 
                WHEN reserve_trucks > 0 THEN 
                    ROUND(reserve_fixed_trucks::numeric / reserve_trucks::numeric, 4)
                ELSE 0
            END AS reserve_fixed_ratio,
            source
        FROM combined
        ORDER BY date;
    """)
