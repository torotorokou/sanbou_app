"""update views for renamed tables

Revision ID: 20251120_150000000
Revises: 20251120_092912697
Create Date: 2025-11-20 15:00:00

テーブルリネーム後のビュー参照を更新します。

背景:
  20251120_091427843: stgテーブルをリネーム (*_shogun_* → shogun_*_*)
  20251120_092912697: rawテーブルをリネーム
  
本マイグレーション:
  - mart.v_shogun_*_daily ビューを新テーブル名に対応
  - 既存のビューを再作成してテーブル参照を更新

対象ビュー:
  - mart.v_shogun_flash_receive_daily  (FROM stg.shogun_flash_receive)
  - mart.v_shogun_flash_yard_daily     (FROM stg.shogun_flash_yard)
  - mart.v_shogun_flash_shipment_daily (FROM stg.shogun_flash_shipment)
  - mart.v_shogun_final_receive_daily  (FROM stg.shogun_final_receive)
  - mart.v_shogun_final_yard_daily     (FROM stg.shogun_final_yard)
  - mart.v_shogun_final_shipment_daily (FROM stg.shogun_final_shipment)
  - mart.v_csv_calendar_daily          (統合ビュー)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251120_150000000'
down_revision = '20251120_092912697'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    リネーム後のテーブル名を参照するようにビューを更新
    """
    
    print("[mart] Updating CSV calendar daily views for renamed tables...")
    
    # -------------------------------------------------------------------------
    # 1. 将軍速報版（FLASH）
    # -------------------------------------------------------------------------
    
    # 受入速報
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_flash_receive_daily AS
        SELECT
            s.slip_date::date              AS data_date,
            'shogun_flash_receive'::text   AS csv_kind,
            COUNT(*)                       AS row_count
        FROM stg.shogun_flash_receive s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    print("✓ Updated mart.v_shogun_flash_receive_daily")
    
    # ヤード速報
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_flash_yard_daily AS
        SELECT
            s.slip_date::date           AS data_date,
            'shogun_flash_yard'::text   AS csv_kind,
            COUNT(*)                    AS row_count
        FROM stg.shogun_flash_yard s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    print("✓ Updated mart.v_shogun_flash_yard_daily")
    
    # 出荷速報
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_flash_shipment_daily AS
        SELECT
            s.slip_date::date               AS data_date,
            'shogun_flash_shipment'::text   AS csv_kind,
            COUNT(*)                        AS row_count
        FROM stg.shogun_flash_shipment s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    print("✓ Updated mart.v_shogun_flash_shipment_daily")
    
    # -------------------------------------------------------------------------
    # 2. 将軍確定版（FINAL）
    # -------------------------------------------------------------------------
    
    # 受入確定
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_final_receive_daily AS
        SELECT
            s.slip_date::date              AS data_date,
            'shogun_final_receive'::text   AS csv_kind,
            COUNT(*)                       AS row_count
        FROM stg.shogun_final_receive s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    print("✓ Updated mart.v_shogun_final_receive_daily")
    
    # ヤード確定
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_final_yard_daily AS
        SELECT
            s.slip_date::date           AS data_date,
            'shogun_final_yard'::text   AS csv_kind,
            COUNT(*)                    AS row_count
        FROM stg.shogun_final_yard s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    print("✓ Updated mart.v_shogun_final_yard_daily")
    
    # 出荷確定
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_final_shipment_daily AS
        SELECT
            s.slip_date::date               AS data_date,
            'shogun_final_shipment'::text   AS csv_kind,
            COUNT(*)                        AS row_count
        FROM stg.shogun_final_shipment s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    print("✓ Updated mart.v_shogun_final_shipment_daily")
    
    # -------------------------------------------------------------------------
    # 3. 統合ビュー（参照先のビューは上で更新済みなので再作成不要）
    # -------------------------------------------------------------------------
    
    # v_csv_calendar_daily は個別ビューをUNION ALLしているだけなので、
    # 個別ビューが更新されれば自動的に新しいテーブルを参照することになる
    # 念のため再作成
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_csv_calendar_daily AS
        SELECT * FROM mart.v_shogun_flash_receive_daily
        UNION ALL
        SELECT * FROM mart.v_shogun_flash_yard_daily
        UNION ALL
        SELECT * FROM mart.v_shogun_flash_shipment_daily
        UNION ALL
        SELECT * FROM mart.v_shogun_final_receive_daily
        UNION ALL
        SELECT * FROM mart.v_shogun_final_yard_daily
        UNION ALL
        SELECT * FROM mart.v_shogun_final_shipment_daily;
    """)
    print("✓ Updated mart.v_csv_calendar_daily")
    
    print("[ok] All CSV calendar views updated for renamed tables")


def downgrade() -> None:
    """
    旧テーブル名を参照するビューに戻す
    """
    
    print("[mart] Reverting CSV calendar daily views to old table names...")
    
    # 受入速報
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_flash_receive_daily AS
        SELECT
            s.slip_date::date              AS data_date,
            'shogun_flash_receive'::text   AS csv_kind,
            COUNT(*)                       AS row_count
        FROM stg.receive_shogun_flash s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    
    # ヤード速報
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_flash_yard_daily AS
        SELECT
            s.slip_date::date           AS data_date,
            'shogun_flash_yard'::text   AS csv_kind,
            COUNT(*)                    AS row_count
        FROM stg.yard_shogun_flash s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    
    # 出荷速報
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_flash_shipment_daily AS
        SELECT
            s.slip_date::date               AS data_date,
            'shogun_flash_shipment'::text   AS csv_kind,
            COUNT(*)                        AS row_count
        FROM stg.shipment_shogun_flash s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    
    # 受入確定
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_final_receive_daily AS
        SELECT
            s.slip_date::date              AS data_date,
            'shogun_final_receive'::text   AS csv_kind,
            COUNT(*)                       AS row_count
        FROM stg.receive_shogun_final s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    
    # ヤード確定
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_final_yard_daily AS
        SELECT
            s.slip_date::date           AS data_date,
            'shogun_final_yard'::text   AS csv_kind,
            COUNT(*)                    AS row_count
        FROM stg.yard_shogun_final s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    
    # 出荷確定
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_shogun_final_shipment_daily AS
        SELECT
            s.slip_date::date               AS data_date,
            'shogun_final_shipment'::text   AS csv_kind,
            COUNT(*)                        AS row_count
        FROM stg.shipment_shogun_final s
        JOIN log.upload_file uf
          ON uf.id = s.upload_file_id
         AND uf.is_deleted = false
        WHERE s.slip_date IS NOT NULL
        GROUP BY s.slip_date::date;
    """)
    
    # 統合ビュー
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_csv_calendar_daily AS
        SELECT * FROM mart.v_shogun_flash_receive_daily
        UNION ALL
        SELECT * FROM mart.v_shogun_flash_yard_daily
        UNION ALL
        SELECT * FROM mart.v_shogun_flash_shipment_daily
        UNION ALL
        SELECT * FROM mart.v_shogun_final_receive_daily
        UNION ALL
        SELECT * FROM mart.v_shogun_final_yard_daily
        UNION ALL
        SELECT * FROM mart.v_shogun_final_shipment_daily;
    """)
    
    print("[ok] Views reverted to old table names")
