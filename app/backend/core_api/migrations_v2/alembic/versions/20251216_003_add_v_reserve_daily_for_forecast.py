"""add_v_reserve_daily_for_forecast

Revision ID: 11e8fe1cc1d4
Revises: 6807c2215b75
Create Date: 2025-12-16 11:22:18.280500

Phase 3: mart.v_reserve_daily_for_forecast ビュー追加

目的：
  予測用の予約日次データを提供（manual優先、なければcustomer集計）

ビュー仕様：
  - manual入力がある日付はmanualを採用
  - manualがない日付はcustomer_dailyを集計
  - どちらもない日は出力しない
  
出力列：
  - date: 予約日
  - reserve_trucks: 予約台数合計
  - reserve_fixed_trucks: 固定客台数
  - reserve_fixed_ratio: 固定客比率（0除算は0）
  - source: データソース（'manual' or 'customer_agg'）

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11e8fe1cc1d4'
down_revision = '6807c2215b75'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """mart.v_reserve_daily_for_forecast ビューを作成"""
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
            -- manual入力データ
            SELECT
                reserve_date AS date,
                total_trucks AS reserve_trucks,
                fixed_trucks AS reserve_fixed_trucks,
                'manual' AS source
            FROM stg.reserve_daily_manual
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
    
    # コメント追加
    op.execute("""
        COMMENT ON VIEW mart.v_reserve_daily_for_forecast IS 
        '予測用の予約日次データ。manual優先、なければcustomer集計。fixed_ratioは0除算を0で処理';
    """)


def downgrade() -> None:
    """mart.v_reserve_daily_for_forecast ビューを削除"""
    op.execute("DROP VIEW IF EXISTS mart.v_reserve_daily_for_forecast CASCADE;")
