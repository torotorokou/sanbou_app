"""update mart receive_daily view to reference stg schema

Revision ID: 20251113_151556000
Revises: 20251113_151137000
Create Date: 2025-11-13 15:15:56.000000

mart.v_receive_daily ビューを更新して stg スキーマを参照するようにする
"""

from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251113_151556000"
down_revision = "20251113_151137000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    mart.v_receive_daily ビューを更新して stg.* テーブルを参照
    """
    # SQLファイルから読み込んで実行
    sql_file = Path(__file__).parent.parent / "sql" / "mart" / "v_receive_daily.sql"
    with open(sql_file, encoding="utf-8") as f:
        sql = f.read()

    op.execute(sql)
    print("✓ Updated mart.v_receive_daily to reference stg schema")


def downgrade() -> None:
    """
    ダウングレード: raw スキーマを参照する元のビューに戻す
    """
    downgrade_sql = """
    CREATE OR REPLACE VIEW mart.v_receive_daily AS
     WITH r_shogun_final AS (
             SELECT s.slip_date AS ddate,
                (sum(s.net_weight) / 1000.0) AS receive_ton,
                count(DISTINCT s.receive_no) AS vehicle_count,
                sum(s.amount) AS sales_yen
               FROM raw.receive_shogun_final s
              WHERE (s.slip_date IS NOT NULL)
              GROUP BY s.slip_date
            ), r_shogun_flash AS (
             SELECT f.slip_date AS ddate,
                (sum(f.net_weight) / 1000.0) AS receive_ton,
                count(DISTINCT f.receive_no) AS vehicle_count,
                sum(f.amount) AS sales_yen
               FROM raw.receive_shogun_flash f
              WHERE (f.slip_date IS NOT NULL)
              GROUP BY f.slip_date
            ), r_king AS (
             SELECT (k.invoice_date)::date AS ddate,
                ((sum(k.net_weight_detail))::numeric / 1000.0) AS receive_ton,
                count(DISTINCT k.invoice_no) AS vehicle_count,
                (sum(k.amount))::numeric AS sales_yen
               FROM raw.receive_king_final k
              WHERE ((k.vehicle_type_code = 1) AND (k.net_weight_detail <> 0))
              GROUP BY (k.invoice_date)::date
            ), r_pick AS (
             SELECT r_shogun_final.ddate,
                r_shogun_final.receive_ton,
                r_shogun_final.vehicle_count,
                r_shogun_final.sales_yen,
                'shogun_final'::text AS source
               FROM r_shogun_final
            UNION ALL
             SELECT f.ddate,
                f.receive_ton,
                f.vehicle_count,
                f.sales_yen,
                'shogun_flash'::text AS text
               FROM r_shogun_flash f
              WHERE (NOT (EXISTS ( SELECT 1
                       FROM r_shogun_final s
                      WHERE (s.ddate = f.ddate))))
            UNION ALL
             SELECT k.ddate,
                k.receive_ton,
                k.vehicle_count,
                k.sales_yen,
                'king'::text AS text
               FROM r_king k
              WHERE ((NOT (EXISTS ( SELECT 1
                       FROM r_shogun_final s
                      WHERE (s.ddate = k.ddate)))) AND (NOT (EXISTS ( SELECT 1
                       FROM r_shogun_flash f
                      WHERE (f.ddate = k.ddate)))))
            )
     SELECT cal.ddate,
        cal.y,
        cal.m,
        cal.iso_year,
        cal.iso_week,
        cal.iso_dow,
        cal.is_business,
        cal.is_holiday,
        cal.day_type,
        (COALESCE(p.receive_ton, (0)::numeric))::numeric(18,3) AS receive_net_ton,
        (COALESCE(p.vehicle_count, (0)::bigint))::integer AS receive_vehicle_count,
        (
            CASE
                WHEN (COALESCE(p.vehicle_count, (0)::bigint) > 0) THEN ((COALESCE(p.receive_ton, (0)::numeric) * 1000.0) / (p.vehicle_count)::numeric)
                ELSE NULL::numeric
            END)::numeric(18,3) AS avg_weight_kg_per_vehicle,
        (COALESCE(p.sales_yen, (0)::numeric))::numeric(18,0) AS sales_yen,
        (
            CASE
                WHEN ((COALESCE(p.receive_ton, (0)::numeric) * 1000.0) > (0)::numeric) THEN (p.sales_yen / (p.receive_ton * 1000.0))
                ELSE NULL::numeric
            END)::numeric(18,3) AS unit_price_yen_per_kg,
        p.source
       FROM (ref.calendar_master cal
         LEFT JOIN r_pick p ON ((cal.ddate = p.ddate)))
      WHERE ((cal.ddate >= '2024-04-01'::date) AND (cal.ddate <= (CURRENT_DATE + '30 days'::interval)))
      ORDER BY cal.ddate;
    """
    op.execute(downgrade_sql)
    print("✓ Reverted mart.v_receive_daily to reference raw schema")
