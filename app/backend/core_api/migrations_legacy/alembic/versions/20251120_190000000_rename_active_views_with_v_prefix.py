"""rename active views with v_ prefix

このマイグレーションは stg.active_* ビューを stg.v_active_* にリネームします。

変更内容:
- stg.active_shogun_flash_receive  → stg.v_active_shogun_flash_receive
- stg.active_shogun_final_receive  → stg.v_active_shogun_final_receive
- stg.active_shogun_flash_yard     → stg.v_active_shogun_flash_yard
- stg.active_shogun_final_yard     → stg.v_active_shogun_final_yard
- stg.active_shogun_flash_shipment → stg.v_active_shogun_flash_shipment
- stg.active_shogun_final_shipment → stg.v_active_shogun_final_shipment

同時に、これらのビューを参照している mart スキーマのビューも更新します。

Revision ID: 20251120_190000000
Revises: 20251120_180000000
Create Date: 2025-11-20 19:00:00.000000
"""

from alembic import op

revision = "20251120_190000000"
down_revision = "20251120_180000000"
branch_labels = None
depends_on = None


# 対象となる将軍テーブル（Flash/Final × Receive/Yard/Shipment）
SHOGUN_TABLES = [
    "shogun_flash_receive",
    "shogun_flash_yard",
    "shogun_flash_shipment",
    "shogun_final_receive",
    "shogun_final_yard",
    "shogun_final_shipment",
]


def upgrade() -> None:
    """
    active_* ビューを v_active_* にリネーム
    """

    print("[stg.v_active_*] Renaming active views to include v_ prefix...")
    print("")

    # ========================================================================
    # Step 1: 新しい名前でビューを作成
    # ========================================================================
    print("[Step 1/3] Creating new views with v_ prefix...")

    for table_name in SHOGUN_TABLES:
        old_view_name = f"active_{table_name}"
        new_view_name = f"v_active_{table_name}"

        # 新しい名前でビューを作成
        sql = f"""
        CREATE OR REPLACE VIEW stg.{new_view_name} AS
        SELECT *
        FROM stg.{table_name}
        WHERE is_deleted = false;
        """

        op.execute(sql)
        print(f"  ✓ Created stg.{new_view_name}")

        # コメントを付与
        comment_sql = f"""
        COMMENT ON VIEW stg.{new_view_name} IS
        'Active rows view: filters out soft-deleted rows (is_deleted = false only).
        Use this view in mart aggregations to automatically exclude deleted data.';
        """
        op.execute(comment_sql)

    print("")

    # ========================================================================
    # Step 2: mart.v_receive_daily を更新（新しいビュー名を使用）
    # ========================================================================
    print("[Step 2/3] Updating mart.v_receive_daily to use new view names...")

    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_receive_daily AS
        WITH r_shogun_final AS (
            SELECT
                s.slip_date AS ddate,
                (SUM(s.net_weight) / 1000.0) AS receive_ton,
                COUNT(DISTINCT s.receive_no) AS vehicle_count,
                SUM(s.amount) AS sales_yen
            FROM stg.v_active_shogun_final_receive s
            WHERE s.slip_date IS NOT NULL
              AND s.is_deleted = false
            GROUP BY s.slip_date
        ),
        r_shogun_flash AS (
            SELECT
                f.slip_date AS ddate,
                (SUM(f.net_weight) / 1000.0) AS receive_ton,
                COUNT(DISTINCT f.receive_no) AS vehicle_count,
                SUM(f.amount) AS sales_yen
            FROM stg.v_active_shogun_flash_receive f
            WHERE f.slip_date IS NOT NULL
              AND f.is_deleted = false
            GROUP BY f.slip_date
        ),
        r_king AS (
            SELECT
                k.invoice_date::date AS ddate,
                (SUM(k.net_weight_detail)::numeric / 1000.0) AS receive_ton,
                COUNT(DISTINCT k.invoice_no) AS vehicle_count,
                SUM(k.amount)::numeric AS sales_yen
            FROM stg.receive_king_final k
            WHERE k.vehicle_type_code = 1
              AND k.net_weight_detail <> 0
            GROUP BY k.invoice_date::date
        ),
        r_pick AS (
            SELECT
                ddate,
                receive_ton,
                vehicle_count,
                sales_yen,
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
            WHERE NOT EXISTS (
                SELECT 1 FROM r_shogun_final s WHERE s.ddate = f.ddate
            )

            UNION ALL

            SELECT
                k.ddate,
                k.receive_ton,
                k.vehicle_count,
                k.sales_yen,
                'king'::text AS source
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
            COALESCE(p.receive_ton, 0::numeric)::numeric(18,3) AS receive_net_ton,
            COALESCE(p.vehicle_count, 0::bigint)::integer AS receive_vehicle_count,
            CASE
                WHEN COALESCE(p.vehicle_count, 0) > 0
                THEN (COALESCE(p.receive_ton, 0) * 1000.0 / p.vehicle_count)
                ELSE NULL
            END::numeric(18,3) AS avg_weight_kg_per_vehicle,
            COALESCE(p.sales_yen, 0::numeric)::numeric(18,0) AS sales_yen,
            CASE
                WHEN (COALESCE(p.receive_ton, 0) * 1000.0) > 0
                THEN (p.sales_yen / (p.receive_ton * 1000.0))
                ELSE NULL
            END::numeric(18,3) AS unit_price_yen_per_kg,
            p.source AS source_system
        FROM ref.v_calendar_classified cal
        LEFT JOIN r_pick p ON p.ddate = cal.ddate
        WHERE cal.ddate <= (NOW() AT TIME ZONE 'Asia/Tokyo')::date - 1
        ORDER BY cal.ddate;
    """
    )

    print("  ✓ Updated mart.v_receive_daily")
    print("")

    # ========================================================================
    # Step 3: 古いビューを削除
    # ========================================================================
    print("[Step 3/3] Dropping old active_* views...")

    for table_name in SHOGUN_TABLES:
        old_view_name = f"active_{table_name}"
        op.execute(f"DROP VIEW IF EXISTS stg.{old_view_name};")
        print(f"  ✓ Dropped stg.{old_view_name}")

    print("")
    print("[stg.v_active_*] Rename completed successfully")
    print("")
    print("📌 Summary:")
    print("  - Created 6 new views with v_ prefix")
    print("  - Updated mart.v_receive_daily to use new view names")
    print("  - Dropped 6 old views without v_ prefix")
    print("")
    print("📌 Next Steps:")
    print("  1. Refresh materialized views: make refresh-mv")
    print("  2. Verify query performance with EXPLAIN ANALYZE")


def downgrade() -> None:
    """
    v_active_* ビューを active_* に戻す
    """

    print("[stg.v_active_*] Reverting view names to remove v_ prefix...")
    print("")

    # Step 1: 古い名前でビューを再作成
    print("[Step 1/3] Recreating views without v_ prefix...")

    for table_name in SHOGUN_TABLES:
        old_view_name = f"active_{table_name}"

        sql = f"""
        CREATE OR REPLACE VIEW stg.{old_view_name} AS
        SELECT *
        FROM stg.{table_name}
        WHERE is_deleted = false;
        """

        op.execute(sql)
        print(f"  ✓ Created stg.{old_view_name}")

    print("")

    # Step 2: mart.v_receive_daily を元に戻す
    print("[Step 2/3] Reverting mart.v_receive_daily...")

    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_receive_daily AS
        WITH r_shogun_final AS (
            SELECT
                s.slip_date AS ddate,
                (SUM(s.net_weight) / 1000.0) AS receive_ton,
                COUNT(DISTINCT s.receive_no) AS vehicle_count,
                SUM(s.amount) AS sales_yen
            FROM stg.active_shogun_final_receive s
            WHERE s.slip_date IS NOT NULL
              AND s.is_deleted = false
            GROUP BY s.slip_date
        ),
        r_shogun_flash AS (
            SELECT
                f.slip_date AS ddate,
                (SUM(f.net_weight) / 1000.0) AS receive_ton,
                COUNT(DISTINCT f.receive_no) AS vehicle_count,
                SUM(f.amount) AS sales_yen
            FROM stg.active_shogun_flash_receive f
            WHERE f.slip_date IS NOT NULL
              AND f.is_deleted = false
            GROUP BY f.slip_date
        ),
        r_king AS (
            SELECT
                k.invoice_date::date AS ddate,
                (SUM(k.net_weight_detail)::numeric / 1000.0) AS receive_ton,
                COUNT(DISTINCT k.invoice_no) AS vehicle_count,
                SUM(k.amount)::numeric AS sales_yen
            FROM stg.receive_king_final k
            WHERE k.vehicle_type_code = 1
              AND k.net_weight_detail <> 0
            GROUP BY k.invoice_date::date
        ),
        r_pick AS (
            SELECT
                ddate,
                receive_ton,
                vehicle_count,
                sales_yen,
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
            WHERE NOT EXISTS (
                SELECT 1 FROM r_shogun_final s WHERE s.ddate = f.ddate
            )

            UNION ALL

            SELECT
                k.ddate,
                k.receive_ton,
                k.vehicle_count,
                k.sales_yen,
                'king'::text AS source
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
            COALESCE(p.receive_ton, 0::numeric)::numeric(18,3) AS receive_net_ton,
            COALESCE(p.vehicle_count, 0::bigint)::integer AS receive_vehicle_count,
            CASE
                WHEN COALESCE(p.vehicle_count, 0) > 0
                THEN (COALESCE(p.receive_ton, 0) * 1000.0 / p.vehicle_count)
                ELSE NULL
            END::numeric(18,3) AS avg_weight_kg_per_vehicle,
            COALESCE(p.sales_yen, 0::numeric)::numeric(18,0) AS sales_yen,
            CASE
                WHEN (COALESCE(p.receive_ton, 0) * 1000.0) > 0
                THEN (p.sales_yen / (p.receive_ton * 1000.0))
                ELSE NULL
            END::numeric(18,3) AS unit_price_yen_per_kg,
            p.source AS source_system
        FROM ref.v_calendar_classified cal
        LEFT JOIN r_pick p ON p.ddate = cal.ddate
        WHERE cal.ddate <= (NOW() AT TIME ZONE 'Asia/Tokyo')::date - 1
        ORDER BY cal.ddate;
    """
    )

    print("  ✓ Reverted mart.v_receive_daily")
    print("")

    # Step 3: 新しいビューを削除
    print("[Step 3/3] Dropping v_active_* views...")

    for table_name in SHOGUN_TABLES:
        new_view_name = f"v_active_{table_name}"
        op.execute(f"DROP VIEW IF EXISTS stg.{new_view_name};")
        print(f"  ✓ Dropped stg.{new_view_name}")

    print("")
    print("[stg.v_active_*] Rollback completed successfully")
