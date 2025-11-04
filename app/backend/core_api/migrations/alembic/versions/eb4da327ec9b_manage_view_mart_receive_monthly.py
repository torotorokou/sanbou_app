"""manage view: mart.receive_monthly

Revision ID: eb4da327ec9b
Revises: 454f7f0472db
Create Date: 2025-11-04 05:54:49.403029
"""
from alembic import op
import sqlalchemy as sa
from textwrap import dedent

# revision identifiers, used by Alembic.
revision = "eb4da327ec9b"
down_revision = "454f7f0472db"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW mart.receive_monthly AS
            WITH d AS (
                SELECT
                    r.ddate,
                    r.y,
                    r.m,
                    r.receive_net_ton,
                    r.receive_vehicle_count,
                    r.sales_yen
                FROM mart.receive_daily AS r
            )
            SELECT
                make_date(y, m, 1)                                               AS month_date,
                to_char(make_date(y, m, 1)::timestamptz, 'YYYY-MM')              AS month,
                y,
                m,
                SUM(receive_net_ton)::numeric(18,3)                               AS receive_net_ton,
                SUM(receive_vehicle_count)                                        AS receive_vehicle_count,
                SUM(sales_yen)::numeric(18,0)                                     AS sales_yen,
                (
                    CASE
                        WHEN SUM(receive_vehicle_count) > 0
                        THEN (SUM(receive_net_ton) * 1000.0) / SUM(receive_vehicle_count)::numeric
                        ELSE NULL::numeric
                    END
                )::numeric(18,3)                                                  AS avg_weight_kg_per_vehicle,
                (
                    CASE
                        WHEN (SUM(receive_net_ton) * 1000.0) > 0::numeric
                        THEN SUM(sales_yen) / (SUM(receive_net_ton) * 1000.0)
                        ELSE NULL::numeric
                    END
                )::numeric(18,3)                                                  AS unit_price_yen_per_kg
            FROM d
            GROUP BY y, m
            ORDER BY y, m;
            """
        )
    )


def downgrade() -> None:
    # 可逆にするなら直前版の CREATE OR REPLACE VIEW 定義を貼る。
    op.execute("DROP VIEW IF EXISTS mart.receive_monthly;")
