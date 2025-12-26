"""update mv_receive_daily to use v_active_shogun views

Purpose:
  Refactor mart.mv_receive_daily to reference stg.v_active_shogun_* views
  instead of direct table references, ensuring automatic is_deleted filtering.

Context:
  - Current: mv_receive_daily references stg.shogun_final_receive/shogun_flash_receive directly
  - Target: Use stg.v_active_shogun_final_receive/v_active_shogun_flash_receive
  - Benefit: Automatic exclusion of soft-deleted data (is_deleted=true)
  - Consistency: Aligns with Upload Calendar, Dashboard, SalesTree implementations

Changes:
  - stg.shogun_final_receive → stg.v_active_shogun_final_receive
  - stg.shogun_flash_receive → stg.v_active_shogun_flash_receive
  - Remove manual "is_deleted = false" checks (handled by views)

Safety:
  - Views already exist (created in 20251120_160000000, renamed in 20251120_190000000)
  - No schema changes, only view reference updates
  - Requires REFRESH MATERIALIZED VIEW after upgrade

Revision ID: 20251211_170000000
Revises: 20251211_160000000
Create Date: 2025-12-11 17:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251211_170000000"
down_revision = "20251211_160000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update mv_receive_daily to use v_active_shogun_* views
    """
    print("[mart.mv_receive_daily] Updating to use v_active_shogun views...")

    # Drop the existing materialized view with CASCADE (dependencies will be recreated)
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_receive_daily CASCADE;")

    # Recreate with v_active_* view references
    op.execute(
        """
        CREATE MATERIALIZED VIEW mart.mv_receive_daily AS
        WITH r_shogun_final AS (
            SELECT
                s.slip_date AS ddate,
                SUM(s.net_weight) / 1000.0 AS receive_ton,
                COUNT(DISTINCT s.receive_no) AS vehicle_count,
                SUM(s.amount) AS sales_yen
            FROM stg.v_active_shogun_final_receive s
            WHERE s.slip_date IS NOT NULL
            GROUP BY s.slip_date
        ),
        r_shogun_flash AS (
            SELECT
                f.slip_date AS ddate,
                SUM(f.net_weight) / 1000.0 AS receive_ton,
                COUNT(DISTINCT f.receive_no) AS vehicle_count,
                SUM(f.amount) AS sales_yen
            FROM stg.v_active_shogun_flash_receive f
            WHERE f.slip_date IS NOT NULL
            GROUP BY f.slip_date
        ),
        r_king AS (
            SELECT
                k.invoice_date::DATE AS ddate,
                (SUM(k.net_weight_detail)::NUMERIC / 1000.0) AS receive_ton,
                COUNT(DISTINCT k.invoice_no) AS vehicle_count,
                SUM(k.amount)::NUMERIC AS sales_yen
            FROM stg.receive_king_final k
            WHERE k.vehicle_type_code = 1
              AND k.net_weight_detail <> 0
            GROUP BY k.invoice_date::DATE
        ),
        r_pick AS (
            -- Priority 1: Shogun Final
            SELECT
                ddate,
                receive_ton,
                vehicle_count,
                sales_yen,
                'shogun_final'::TEXT AS source
            FROM r_shogun_final

            UNION ALL

            -- Priority 2: Shogun Flash (if Final doesn't exist for that date)
            SELECT
                f.ddate,
                f.receive_ton,
                f.vehicle_count,
                f.sales_yen,
                'shogun_flash'::TEXT AS source
            FROM r_shogun_flash f
            WHERE NOT EXISTS (
                SELECT 1 FROM r_shogun_final s WHERE s.ddate = f.ddate
            )

            UNION ALL

            -- Priority 3: King (if neither Final nor Flash exists)
            SELECT
                k.ddate,
                k.receive_ton,
                k.vehicle_count,
                k.sales_yen,
                'king'::TEXT AS source
            FROM r_king k
            WHERE NOT EXISTS (
                SELECT 1 FROM r_shogun_final s WHERE s.ddate = k.ddate
            )
            AND NOT EXISTS (
                SELECT 1 FROM r_shogun_flash f WHERE f.ddate = k.ddate
            )
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
            COALESCE(p.receive_ton, 0)::NUMERIC(18,3) AS receive_net_ton,
            COALESCE(p.vehicle_count, 0)::INTEGER AS receive_vehicle_count,
            CASE
                WHEN COALESCE(p.vehicle_count, 0) > 0
                THEN (COALESCE(p.receive_ton, 0) * 1000.0 / p.vehicle_count)
                ELSE NULL
            END::NUMERIC(18,3) AS avg_weight_kg_per_vehicle,
            COALESCE(p.sales_yen, 0)::NUMERIC(18,0) AS sales_yen,
            CASE
                WHEN (COALESCE(p.receive_ton, 0) * 1000.0) > 0
                THEN (p.sales_yen / (p.receive_ton * 1000.0))
                ELSE NULL
            END::NUMERIC(18,3) AS unit_price_yen_per_kg,
            p.source AS source_system
        FROM ref.v_calendar_classified cal
        LEFT JOIN r_pick p ON p.ddate = cal.ddate
        WHERE cal.ddate <= (NOW() AT TIME ZONE 'Asia/Tokyo')::DATE - 1
        ORDER BY cal.ddate;
    """
    )

    # Refresh the materialized view with current data
    print("[mart.mv_receive_daily] Refreshing materialized view...")
    op.execute("REFRESH MATERIALIZED VIEW mart.mv_receive_daily;")

    # Recreate dependent views (dropped by CASCADE)
    print("[mart] Recreating dependent views...")

    # v_receive_daily (wrapper view)
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_receive_daily AS
        SELECT * FROM mart.mv_receive_daily;
    """
    )

    # v_receive_weekly
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_receive_weekly AS
        SELECT
            iso_year,
            iso_week,
            MIN(ddate) AS week_start,
            MAX(ddate) AS week_end,
            SUM(receive_net_ton) AS receive_net_ton,
            SUM(receive_vehicle_count) AS receive_vehicle_count,
            SUM(sales_yen) AS sales_yen,
            COUNT(*) FILTER (WHERE is_business = true) AS business_days,
            COUNT(*) AS total_days
        FROM mart.mv_receive_daily
        GROUP BY iso_year, iso_week
        ORDER BY iso_year, iso_week;
    """
    )

    # v_receive_monthly
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_receive_monthly AS
        SELECT
            y,
            m,
            MIN(ddate) AS month_start,
            MAX(ddate) AS month_end,
            SUM(receive_net_ton) AS receive_net_ton,
            SUM(receive_vehicle_count) AS receive_vehicle_count,
            SUM(sales_yen) AS sales_yen,
            COUNT(*) FILTER (WHERE is_business = true) AS business_days,
            COUNT(*) AS total_days
        FROM mart.mv_receive_daily
        GROUP BY y, m
        ORDER BY y, m;
    """
    )

    print("[mart.mv_receive_daily] ✅ Successfully updated to use v_active views")
    print("")
    print("📌 Changes:")
    print("  - stg.shogun_final_receive → stg.v_active_shogun_final_receive")
    print("  - stg.shogun_flash_receive → stg.v_active_shogun_flash_receive")
    print("  - Automatic is_deleted=false filtering via views")
    print("  - Dependent views recreated: v_receive_daily, v_receive_weekly, v_receive_monthly")


def downgrade() -> None:
    """
    Revert mv_receive_daily to use direct table references
    """
    print("[mart.mv_receive_daily] Reverting to direct table references...")

    # Drop the view-based materialized view (CASCADE to drop dependent views)
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_receive_daily CASCADE;")

    # Recreate with direct table references (original version)
    op.execute(
        """
        CREATE MATERIALIZED VIEW mart.mv_receive_daily AS
        WITH r_shogun_final AS (
            SELECT
                s.slip_date AS ddate,
                SUM(s.net_weight) / 1000.0 AS receive_ton,
                COUNT(DISTINCT s.receive_no) AS vehicle_count,
                SUM(s.amount) AS sales_yen
            FROM stg.shogun_final_receive s
            WHERE s.slip_date IS NOT NULL
            GROUP BY s.slip_date
        ),
        r_shogun_flash AS (
            SELECT
                f.slip_date AS ddate,
                SUM(f.net_weight) / 1000.0 AS receive_ton,
                COUNT(DISTINCT f.receive_no) AS vehicle_count,
                SUM(f.amount) AS sales_yen
            FROM stg.shogun_flash_receive f
            WHERE f.slip_date IS NOT NULL
            GROUP BY f.slip_date
        ),
        r_king AS (
            SELECT
                k.invoice_date::DATE AS ddate,
                (SUM(k.net_weight_detail)::NUMERIC / 1000.0) AS receive_ton,
                COUNT(DISTINCT k.invoice_no) AS vehicle_count,
                SUM(k.amount)::NUMERIC AS sales_yen
            FROM stg.receive_king_final k
            WHERE k.vehicle_type_code = 1
              AND k.net_weight_detail <> 0
            GROUP BY k.invoice_date::DATE
        ),
        r_pick AS (
            SELECT
                ddate,
                receive_ton,
                vehicle_count,
                sales_yen,
                'shogun_final'::TEXT AS source
            FROM r_shogun_final

            UNION ALL

            SELECT
                f.ddate,
                f.receive_ton,
                f.vehicle_count,
                f.sales_yen,
                'shogun_flash'::TEXT AS source
            FROM r_shogun_flash f
            WHERE NOT EXISTS (
                SELECT 1 FROM r_shogun_final s WHERE s.ddate = f.ddate
            )

            UNION ALL

            SELECT
                k.ddate,
                k.receive_ton,
                k.vehicle_count,
                k.sales_yen,
                'king'::TEXT AS source
            FROM r_king k
            WHERE NOT EXISTS (
                SELECT 1 FROM r_shogun_final s WHERE s.ddate = k.ddate
            )
            AND NOT EXISTS (
                SELECT 1 FROM r_shogun_flash f WHERE f.ddate = k.ddate
            )
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
            COALESCE(p.receive_ton, 0)::NUMERIC(18,3) AS receive_net_ton,
            COALESCE(p.vehicle_count, 0)::INTEGER AS receive_vehicle_count,
            CASE
                WHEN COALESCE(p.vehicle_count, 0) > 0
                THEN (COALESCE(p.receive_ton, 0) * 1000.0 / p.vehicle_count)
                ELSE NULL
            END::NUMERIC(18,3) AS avg_weight_kg_per_vehicle,
            COALESCE(p.sales_yen, 0)::NUMERIC(18,0) AS sales_yen,
            CASE
                WHEN (COALESCE(p.receive_ton, 0) * 1000.0) > 0
                THEN (p.sales_yen / (p.receive_ton * 1000.0))
                ELSE NULL
            END::NUMERIC(18,3) AS unit_price_yen_per_kg,
            p.source AS source_system
        FROM ref.v_calendar_classified cal
        LEFT JOIN r_pick p ON p.ddate = cal.ddate
        WHERE cal.ddate <= (NOW() AT TIME ZONE 'Asia/Tokyo')::DATE - 1
        ORDER BY cal.ddate;
    """
    )

    # Refresh the materialized view
    op.execute("REFRESH MATERIALIZED VIEW mart.mv_receive_daily;")

    # Recreate dependent views (dropped by CASCADE)
    print("[mart] Recreating dependent views...")

    # v_receive_daily (wrapper view)
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_receive_daily AS
        SELECT * FROM mart.mv_receive_daily;
    """
    )

    # v_receive_weekly
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_receive_weekly AS
        SELECT
            iso_year,
            iso_week,
            MIN(ddate) AS week_start,
            MAX(ddate) AS week_end,
            SUM(receive_net_ton) AS receive_net_ton,
            SUM(receive_vehicle_count) AS receive_vehicle_count,
            SUM(sales_yen) AS sales_yen,
            COUNT(*) FILTER (WHERE is_business = true) AS business_days,
            COUNT(*) AS total_days
        FROM mart.mv_receive_daily
        GROUP BY iso_year, iso_week
        ORDER BY iso_year, iso_week;
    """
    )

    # v_receive_monthly
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_receive_monthly AS
        SELECT
            y,
            m,
            MIN(ddate) AS month_start,
            MAX(ddate) AS month_end,
            SUM(receive_net_ton) AS receive_net_ton,
            SUM(receive_vehicle_count) AS receive_vehicle_count,
            SUM(sales_yen) AS sales_yen,
            COUNT(*) FILTER (WHERE is_business = true) AS business_days,
            COUNT(*) AS total_days
        FROM mart.mv_receive_daily
        GROUP BY y, m
        ORDER BY y, m;
    """
    )

    print("[mart.mv_receive_daily] ✅ Reverted to direct table references")
