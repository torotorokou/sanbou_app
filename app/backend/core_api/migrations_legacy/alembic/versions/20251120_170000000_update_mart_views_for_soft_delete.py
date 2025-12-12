"""update mart views to filter soft deleted rows

このマイグレーションは mart スキーマのビュー/マテビューを更新し、
論理削除された行（is_deleted = true）を集計から除外します。

変更対象:
1. mart.v_receive_daily
   - stg.shogun_final_receive → stg.active_shogun_final_receive に変更
   - stg.shogun_flash_receive → stg.active_shogun_flash_receive に変更
   
2. mart.v_shogun_flash_receive_daily
   - WHERE 句に is_deleted = false 条件を追加
   
3. mart.v_shogun_final_receive_daily
   - WHERE 句に is_deleted = false 条件を追加

4. マテリアライズドビューの再定義（変更後に REFRESH が必要）
   - mart.mv_target_card_per_day
   - mart.mv_inb5y_week_profile_min
   - mart.mv_inb_avg5y_day_biz
   - mart.mv_inb_avg5y_weeksum_biz
   - mart.mv_inb_avg5y_day_scope

設計方針:
- stg.active_* ビューを使用することで、is_deleted フィルタを自動適用
- WHERE 句での直接フィルタも併用（明示的な条件として残す）

Revision ID: 20251120_170000000
Revises: 20251120_160000000
Create Date: 2025-11-20 17:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "20251120_170000000"
down_revision = "20251120_160000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    mart スキーマのビュー/マテビューを更新し、is_deleted = false の行のみを集計対象にする
    """
    
    print("[mart.*] Updating views to filter soft-deleted rows...")
    
    # ========================================================================
    # 1. mart.v_receive_daily の更新
    #    - stg.shogun_* → stg.active_shogun_* に変更
    #    - is_deleted = false 条件を明示的に追加（防御的プログラミング）
    # ========================================================================
    print("  -> Updating mart.v_receive_daily")
    
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_receive_daily AS
        WITH r_shogun_final AS (
            SELECT
                s.slip_date AS ddate,
                (SUM(s.net_weight) / 1000.0) AS receive_ton,
                COUNT(DISTINCT s.receive_no) AS vehicle_count,
                SUM(s.amount) AS sales_yen
            FROM stg.active_shogun_final_receive s
            WHERE s.slip_date IS NOT NULL
              AND s.is_deleted = false  -- 明示的にフィルタ（active_* ビュー経由でも保証される）
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
              AND f.is_deleted = false  -- 明示的にフィルタ
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
            -- 優先順位1: shogun_final（最終版が最優先）
            SELECT
                ddate,
                receive_ton,
                vehicle_count,
                sales_yen,
                'shogun_final'::text AS source
            FROM r_shogun_final
            
            UNION ALL
            
            -- 優先順位2: shogun_flash（最終版がない日のみ）
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
            
            -- 優先順位3: king（将軍データがない日のみ）
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
    """)
    
    print("    ✓ Updated mart.v_receive_daily (using stg.active_* views)")
    
    # ========================================================================
    # 2. mart.v_shogun_flash_receive_daily の更新
    # ========================================================================
    print("  -> Updating mart.v_shogun_flash_receive_daily")
    
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_flash_receive_daily AS
        SELECT
            s.slip_date AS data_date,
            'shogun_flash_receive'::text AS csv_kind,
            COUNT(*) AS row_count
        FROM stg.shogun_flash_receive s
        JOIN log.upload_file uf ON uf.id = s.upload_file_id AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
          AND s.is_deleted = false  -- 論理削除された行を除外
        GROUP BY s.slip_date;
    """)
    
    print("    ✓ Updated mart.v_shogun_flash_receive_daily")
    
    # ========================================================================
    # 3. mart.v_shogun_final_receive_daily の更新
    # ========================================================================
    print("  -> Updating mart.v_shogun_final_receive_daily")
    
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_final_receive_daily AS
        SELECT
            s.slip_date AS data_date,
            'shogun_final_receive'::text AS csv_kind,
            COUNT(*) AS row_count
        FROM stg.shogun_final_receive s
        JOIN log.upload_file uf ON uf.id = s.upload_file_id AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
          AND s.is_deleted = false  -- 論理削除された行を除外
        GROUP BY s.slip_date;
    """)
    
    print("    ✓ Updated mart.v_shogun_final_receive_daily")
    
    # ========================================================================
    # 4. マテリアライズドビューは定義を変更せず、REFRESH のみ実行
    #    （v_receive_daily の変更が自動的に反映される）
    # ========================================================================
    print("")
    print("📌 マテリアライズドビューのリフレッシュが必要です:")
    print("   REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;")
    print("   REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb5y_week_profile_min;")
    print("   REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb_avg5y_day_biz;")
    print("   REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb_avg5y_weeksum_biz;")
    print("   REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb_avg5y_day_scope;")
    print("")
    print("   または: make refresh-mv")
    print("")
    print("[mart.*] View update completed successfully")


def downgrade() -> None:
    """
    ビューを元の定義に戻す（active_* ビューを使用しない版）
    """
    
    print("[mart.*] Reverting views to original definitions...")
    
    # mart.v_receive_daily を元に戻す
    print("  -> Reverting mart.v_receive_daily")
    
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_receive_daily AS
        WITH r_shogun_final AS (
            SELECT
                s.slip_date AS ddate,
                (SUM(s.net_weight) / 1000.0) AS receive_ton,
                COUNT(DISTINCT s.receive_no) AS vehicle_count,
                SUM(s.amount) AS sales_yen
            FROM stg.shogun_final_receive s
            WHERE s.slip_date IS NOT NULL
            GROUP BY s.slip_date
        ),
        r_shogun_flash AS (
            SELECT
                f.slip_date AS ddate,
                (SUM(f.net_weight) / 1000.0) AS receive_ton,
                COUNT(DISTINCT f.receive_no) AS vehicle_count,
                SUM(f.amount) AS sales_yen
            FROM stg.shogun_flash_receive f
            WHERE f.slip_date IS NOT NULL
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
    """)
    
    # mart.v_shogun_flash_receive_daily を元に戻す
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_flash_receive_daily AS
        SELECT
            s.slip_date AS data_date,
            'shogun_flash_receive'::text AS csv_kind,
            COUNT(*) AS row_count
        FROM stg.shogun_flash_receive s
        JOIN log.upload_file uf ON uf.id = s.upload_file_id AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date;
    """)
    
    # mart.v_shogun_final_receive_daily を元に戻す
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_final_receive_daily AS
        SELECT
            s.slip_date AS data_date,
            'shogun_final_receive'::text AS csv_kind,
            COUNT(*) AS row_count
        FROM stg.shogun_final_receive s
        JOIN log.upload_file uf ON uf.id = s.upload_file_id AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date;
    """)
    
    print("[mart.*] Views reverted successfully")
