"""update v_reserve_daily_features with manual customer count

Revision ID: 20251219_003
Revises: 20251219_002
Create Date: 2025-12-19 12:10:00.000000

Purpose:
- Update mart.v_reserve_daily_features to use manual customer count when available
- Prioritize manual input over customer_agg for total_customer_count and fixed_customer_count
- Maintain backward compatibility (COALESCE to customer_agg when manual is NULL)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251219_003'
down_revision: Union[str, None] = '20251219_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update mart.v_reserve_daily_features to use manual customer count"""
    
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_reserve_daily_features AS
        WITH customer_agg AS (
            SELECT 
                reserve_date AS date,
                COUNT(*) AS total_customer_count,
                COUNT(*) FILTER (WHERE is_fixed_customer) AS fixed_customer_count,
                SUM(planned_trucks) AS reserve_trucks,
                SUM(CASE WHEN is_fixed_customer THEN planned_trucks ELSE 0 END) AS reserve_fixed_trucks,
                'customer_agg'::text AS source
            FROM stg.reserve_customer_daily
            GROUP BY reserve_date
        ),
        manual_data AS (
            SELECT 
                reserve_date AS date,
                total_customer_count,   -- ← Changed from NULL::bigint
                fixed_customer_count,   -- ← Changed from NULL::bigint
                total_trucks AS reserve_trucks,
                fixed_trucks AS reserve_fixed_trucks,
                'manual'::text AS source
            FROM stg.reserve_daily_manual
            WHERE deleted_at IS NULL
        ),
        combined AS (
            SELECT 
                COALESCE(m.date, c.date) AS date,
                -- Prioritize manual customer count, fallback to customer_agg
                COALESCE(m.total_customer_count, c.total_customer_count, 0) AS total_customer_count,
                COALESCE(m.fixed_customer_count, c.fixed_customer_count, 0) AS fixed_customer_count,
                -- Prioritize manual trucks, fallback to customer_agg
                COALESCE(m.reserve_trucks, c.reserve_trucks, 0) AS reserve_trucks,
                COALESCE(m.reserve_fixed_trucks, c.reserve_fixed_trucks, 0) AS reserve_fixed_trucks,
                -- Source priority: manual > customer_agg
                CASE 
                    WHEN m.date IS NOT NULL AND (
                        m.total_customer_count IS NOT NULL 
                        OR m.fixed_customer_count IS NOT NULL 
                        OR m.reserve_trucks IS NOT NULL
                    ) THEN 'manual'
                    ELSE COALESCE(c.source, 'none')
                END AS source
            FROM manual_data m
            FULL OUTER JOIN customer_agg c ON m.date = c.date
            WHERE COALESCE(m.date, c.date) IS NOT NULL
        )
        SELECT 
            date,
            total_customer_count,
            fixed_customer_count,
            CASE 
                WHEN total_customer_count > 0 
                THEN ROUND(fixed_customer_count::numeric / total_customer_count::numeric, 4)
                ELSE 0::numeric
            END AS fixed_customer_ratio,
            reserve_trucks,
            reserve_fixed_trucks,
            CASE 
                WHEN reserve_trucks > 0 
                THEN ROUND(reserve_fixed_trucks::numeric / reserve_trucks::numeric, 4)
                ELSE 0::numeric
            END AS reserve_fixed_trucks_ratio,
            source
        FROM combined
        ORDER BY date;
    """)
    
    # Add comment to view
    op.execute("""
        COMMENT ON VIEW mart.v_reserve_daily_features IS
        '予約データの日次特徴量ビュー（企業数＋台数）
         - total_customer_count: 予約企業数（manual優先、なければcustomer_aggから算出）
         - fixed_customer_count: 固定客企業数（同上）
         - fixed_customer_ratio: 固定客企業比率（fixed/total）
         - reserve_trucks: 予約台数（manual優先、なければcustomer_aggから算出）
         - reserve_fixed_trucks: 固定客台数（同上）
         - reserve_fixed_trucks_ratio: 固定客台数比率（reserve_fixed_trucks/reserve_trucks）
         - source: データソース（manual or customer_agg）';
    """)


def downgrade() -> None:
    """Revert mart.v_reserve_daily_features to original definition"""
    
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_reserve_daily_features AS
        WITH customer_agg AS (
            SELECT 
                reserve_date AS date,
                COUNT(*) AS total_customer_count,
                COUNT(DISTINCT CASE WHEN is_fixed_customer THEN customer_cd ELSE NULL END) AS fixed_customer_count,
                SUM(planned_trucks) AS reserve_trucks,
                SUM(CASE WHEN is_fixed_customer THEN planned_trucks ELSE 0 END) AS reserve_fixed_trucks,
                'customer_agg'::text AS source
            FROM stg.reserve_customer_daily
            GROUP BY reserve_date
        ),
        manual_data AS (
            SELECT 
                reserve_date AS date,
                NULL::bigint AS total_customer_count,   -- ← Reverted to NULL
                NULL::bigint AS fixed_customer_count,   -- ← Reverted to NULL
                total_trucks AS reserve_trucks,
                fixed_trucks AS reserve_fixed_trucks,
                'manual'::text AS source
            FROM stg.reserve_daily_manual
            WHERE deleted_at IS NULL
        ),
        combined AS (
            SELECT 
                COALESCE(m.date, c.date) AS date,
                COALESCE(c.total_customer_count, 0) AS total_customer_count,
                COALESCE(c.fixed_customer_count, 0) AS fixed_customer_count,
                COALESCE(m.reserve_trucks, c.reserve_trucks, 0) AS reserve_trucks,
                COALESCE(m.reserve_fixed_trucks, c.reserve_fixed_trucks, 0) AS reserve_fixed_trucks,
                COALESCE(m.source, c.source) AS source
            FROM manual_data m
            FULL OUTER JOIN customer_agg c ON m.date = c.date
            WHERE COALESCE(m.date, c.date) IS NOT NULL
        )
        SELECT 
            date,
            total_customer_count,
            fixed_customer_count,
            CASE 
                WHEN total_customer_count > 0 
                THEN ROUND(fixed_customer_count::numeric / total_customer_count::numeric, 4)
                ELSE 0::numeric
            END AS fixed_customer_ratio,
            reserve_trucks,
            reserve_fixed_trucks,
            CASE 
                WHEN reserve_trucks > 0 
                THEN ROUND(reserve_fixed_trucks::numeric / reserve_trucks::numeric, 4)
                ELSE 0::numeric
            END AS reserve_fixed_trucks_ratio,
            source
        FROM combined
        ORDER BY date;
    """)
