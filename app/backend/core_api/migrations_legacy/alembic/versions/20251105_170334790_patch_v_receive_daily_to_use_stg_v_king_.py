"""patch v_receive_daily to use stg.v_king_receive_clean

Revision ID: 20251105_170334790
Revises: 20251105_165932182
Create Date: 2025-11-05 08:03:35.569011

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251105_170334790"
down_revision = "20251105_165932182"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
    CREATE OR REPLACE VIEW mart.v_receive_daily AS
    WITH r_shogun_final AS (
      SELECT
        s.slip_date AS ddate,
        SUM(s.net_weight) / 1000.0               AS receive_ton,
        COUNT(DISTINCT s.receive_no)             AS vehicle_count,
        SUM(s.amount)                            AS sales_yen
      FROM raw.receive_shogun_final s
      WHERE s.slip_date IS NOT NULL
      GROUP BY s.slip_date
    ),
    r_shogun_flash AS (
      SELECT
        f.slip_date AS ddate,
        SUM(f.net_weight) / 1000.0               AS receive_ton,
        COUNT(DISTINCT f.receive_no)             AS vehicle_count,
        SUM(f.amount)                            AS sales_yen
      FROM raw.receive_shogun_flash f
      WHERE f.slip_date IS NOT NULL
      GROUP BY f.slip_date
    ),
    -- ★ここを raw から stg に差し替え
    r_king AS (
      SELECT
        k.invoice_d                               AS ddate,
        SUM(k.net_weight_detail)::numeric/1000.0  AS receive_ton,
        COUNT(DISTINCT k.invoice_no)              AS vehicle_count,
        SUM(k.amount)::numeric                    AS sales_yen
      FROM stg.v_king_receive_clean k
      GROUP BY k.invoice_d
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
        'shogun_flash'::text AS source
      FROM r_shogun_flash f
      WHERE NOT EXISTS (SELECT 1 FROM r_shogun_final s WHERE s.ddate = f.ddate)

      UNION ALL
      SELECT
        k.ddate,
        k.receive_ton,
        k.vehicle_count,
        k.sales_yen,
        'king'::text AS source
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
      COALESCE(p.receive_ton, 0)::numeric(18,3)        AS receive_net_ton,
      COALESCE(p.vehicle_count, 0)::integer             AS receive_vehicle_count,
      CASE WHEN COALESCE(p.vehicle_count,0) > 0
           THEN (COALESCE(p.receive_ton,0) * 1000.0) / p.vehicle_count::numeric
           ELSE NULL
      END::numeric(18,3)                                AS avg_weight_kg_per_vehicle,
      COALESCE(p.sales_yen, 0)::numeric(18,0)           AS sales_yen,
      CASE WHEN (COALESCE(p.receive_ton,0) * 1000.0) > 0
           THEN p.sales_yen / (p.receive_ton * 1000.0)
           ELSE NULL
      END::numeric(18,3)                                AS unit_price_yen_per_kg,
      p.source                                          AS source_system
    FROM ref.v_calendar_classified cal
    LEFT JOIN r_pick p ON p.ddate = cal.ddate
    WHERE cal.ddate <= ((now() AT TIME ZONE 'Asia/Tokyo')::date - 1)
    ORDER BY cal.ddate;
    """
    )


def downgrade():

    pass
