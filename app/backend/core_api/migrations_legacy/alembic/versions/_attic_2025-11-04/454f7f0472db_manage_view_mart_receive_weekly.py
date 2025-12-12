"""manage view: mart.receive_weekly

Revision ID: 454f7f0472db
Revises: d64c705dde4a
Create Date: 2025-11-04 05:25:44.915519

"""
from alembic import op
import sqlalchemy as sa
from textwrap import dedent


# revision identifiers, used by Alembic.
revision = '454f7f0472db'
down_revision = 'd64c705dde4a'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute(dedent("""
        CREATE OR REPLACE VIEW mart.receive_weekly AS
        WITH w AS (
            SELECT
                d.iso_year,
                d.iso_week,
                MIN(d.ddate)                                         AS week_start_date,
                MAX(d.ddate)                                         AS week_end_date,
                SUM(d.receive_net_ton)::numeric(18,3)                AS receive_net_ton,
                SUM(d.receive_vehicle_count)                         AS receive_vehicle_count,
                SUM(d.sales_yen)::numeric(18,0)                      AS sales_yen
            FROM mart.receive_daily AS d
            GROUP BY d.iso_year, d.iso_week
        )
        SELECT
            iso_year,
            iso_week,
            iso_year * 100 + iso_week                               AS iso_yearweek_key,
            week_start_date,
            week_end_date,
            to_char(
                make_date(iso_year, 1, 4)
                + (iso_week - 1)::double precision * interval '7 days'
                - (extract(isodow from make_date(iso_year, 1, 4))::int - 1)::double precision * interval '1 day',
                '"W"IW'
            )                                                       AS week_label_simple,
            to_char(week_start_date::timestamptz, 'YYYY-"W"IW')     AS week_label_i18n,
            receive_net_ton,
            receive_vehicle_count,
            sales_yen,
            (
                CASE
                    WHEN receive_vehicle_count > 0
                    THEN (receive_net_ton * 1000.0) / receive_vehicle_count::numeric
                    ELSE NULL::numeric
                END
            )::numeric(18,3)                                        AS avg_weight_kg_per_vehicle,
            (
                CASE
                    WHEN (receive_net_ton * 1000.0) > 0::numeric
                    THEN sales_yen / (receive_net_ton * 1000.0)
                    ELSE NULL::numeric
                END
            )::numeric(18,3)                                        AS unit_price_yen_per_kg
        FROM w
        ORDER BY iso_year, iso_week;
    """))


def downgrade() -> None:
    # 可逆にしたい場合は直前版の CREATE OR REPLACE VIEW をここに記述
    op.execute("DROP VIEW IF EXISTS mart.receive_weekly;")