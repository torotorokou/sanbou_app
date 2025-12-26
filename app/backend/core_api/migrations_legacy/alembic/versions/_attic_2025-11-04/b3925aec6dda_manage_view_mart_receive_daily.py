"""manage view: mart.receive_daily

Revision ID: b3925aec6dda
Revises: eb4da327ec9b
Create Date: 2025-11-04 05:59:53.726364
"""

from textwrap import dedent

import sqlalchemy as sa  # noqa: F401  (kept for consistency with other revisions)
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3925aec6dda"
down_revision = "eb4da327ec9b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW mart.receive_daily AS
            WITH r_shogun_final AS (
                SELECT
                    s.slip_date AS ddate,
                    SUM(s.net_weight) / 1000.0                 AS receive_ton,
                    COUNT(DISTINCT s.receive_no)               AS vehicle_count,
                    SUM(s.amount)                              AS sales_yen
                FROM raw.receive_shogun_final s
                WHERE s.slip_date IS NOT NULL
                GROUP BY s.slip_date
            ),
            r_shogun_flash AS (
                SELECT
                    f.slip_date AS ddate,
                    SUM(f.net_weight) / 1000.0                 AS receive_ton,
                    COUNT(DISTINCT f.receive_no)               AS vehicle_count,
                    SUM(f.amount)                              AS sales_yen
                FROM raw.receive_shogun_flash f
                WHERE f.slip_date IS NOT NULL
                GROUP BY f.slip_date
            ),
            r_king AS (
                SELECT
                    k.invoice_date::date                       AS ddate,
                    SUM(k.net_weight_detail)::numeric / 1000.0 AS receive_ton,
                    COUNT(DISTINCT k.invoice_no)               AS vehicle_count,
                    SUM(k.amount)::numeric                     AS sales_yen
                FROM raw.receive_king_final k
                WHERE k.vehicle_type_code = 1
                  AND k.net_weight_detail <> 0
                GROUP BY (k.invoice_date::date)
            ),
            r_pick AS (
                SELECT
                    r_shogun_final.ddate,
                    r_shogun_final.receive_ton,
                    r_shogun_final.vehicle_count,
                    r_shogun_final.sales_yen,
                    'shogun_final'::text AS source
                FROM r_shogun_final
                UNION ALL
                SELECT
                    f.ddate,
                    f.receive_ton,
                    f.vehicle_count,
                    f.sales_yen,
                    'shogun_flash'::text AS text
                FROM r_shogun_flash f
                WHERE NOT EXISTS (SELECT 1 FROM r_shogun_final s WHERE s.ddate = f.ddate)
                UNION ALL
                SELECT
                    k.ddate,
                    k.receive_ton,
                    k.vehicle_count,
                    k.sales_yen,
                    'king'::text AS text
                FROM r_king k
                WHERE NOT EXISTS (SELECT 1 FROM r_shogun_final s WHERE s.ddate = k.ddate)
                  AND NOT EXISTS (SELECT 1 FROM r_shogun_flash f WHERE f.ddate = k.ddate)
            )
            SELECT
                cal.ddate,
                cal.y,
                cal.m,
                cal.iso_year,
                cal.iso_week,
                cal.iso_dow,
                cal.is_business,
                cal.is_holiday,
                cal.day_type,
                COALESCE(p.receive_ton, 0::numeric)::numeric(18,3)       AS receive_net_ton,
                COALESCE(p.vehicle_count, 0::bigint)::integer            AS receive_vehicle_count,
                (
                    CASE
                        WHEN COALESCE(p.vehicle_count, 0::bigint) > 0
                        THEN COALESCE(p.receive_ton, 0::numeric) * 1000.0 / p.vehicle_count::numeric
                        ELSE NULL::numeric
                    END
                )::numeric(18,3)                                         AS avg_weight_kg_per_vehicle,
                COALESCE(p.sales_yen, 0::numeric)::numeric(18,0)         AS sales_yen,
                (
                    CASE
                        WHEN (COALESCE(p.receive_ton, 0::numeric) * 1000.0) > 0::numeric
                        THEN p.sales_yen / (p.receive_ton * 1000.0)
                        ELSE NULL::numeric
                    END
                )::numeric(18,3)                                         AS unit_price_yen_per_kg,
                p.source                                                 AS source_system
            FROM ref.v_calendar_classified cal
            LEFT JOIN r_pick p
              ON p.ddate = cal.ddate
            WHERE cal.ddate <= ((NOW() AT TIME ZONE 'Asia/Tokyo')::date - 1)
            ORDER BY cal.ddate;
            """
        )
    )


def downgrade() -> None:
    # 直前版の定義に厳密に戻す必要がある場合は、ここにその CREATE OR REPLACE VIEW を書く。
    # 簡易には DROP VIEW で管理から外す。
    op.execute("DROP VIEW IF EXISTS mart.receive_daily;")
