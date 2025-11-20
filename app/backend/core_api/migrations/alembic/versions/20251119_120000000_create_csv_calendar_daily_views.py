"""create mart daily csv calendar views

このマイグレーションは CSV アップロードカレンダー用の日次集計ビューを作成します。

構成:
1. 各 stg テーブルごとの日次集計ビュー (8個)
   - stg.receive_shogun_flash → mart.v_shogun_flash_receive_daily
   - stg.yard_shogun_flash → mart.v_shogun_flash_yard_daily
   - stg.shipment_shogun_flash → mart.v_shogun_flash_shipment_daily
   - stg.receive_shogun_final → mart.v_shogun_final_receive_daily
   - stg.yard_shogun_final → mart.v_shogun_final_yard_daily
   - stg.shipment_shogun_final → mart.v_shogun_final_shipment_daily

2. 統合ビュー mart.v_csv_calendar_daily
   - 上記すべてを UNION ALL で結合
   - カラム: data_date (date), csv_kind (text), row_count (bigint)

仕様:
- log.upload_file との JOIN で is_deleted=false のレコードのみ集計
- 論理削除されたファイルのデータはカレンダーから除外される
- slip_date::date で日付を集約

Revision ID: 20251119_120000000
Revises: 20251119_110000000
Create Date: 2025-11-19 12:00:00.000000
"""
from alembic import op


revision = "20251119_120000000"
down_revision = "20251119_110000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    CSV カレンダー用の日次集計ビューを作成
    """
    
    print("[mart] Creating CSV calendar daily views...")
    
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
    print("✓ Created mart.v_shogun_flash_receive_daily")
    
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
    print("✓ Created mart.v_shogun_flash_yard_daily")
    
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
    print("✓ Created mart.v_shogun_flash_shipment_daily")
    
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
    print("✓ Created mart.v_shogun_final_receive_daily")
    
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
    print("✓ Created mart.v_shogun_final_yard_daily")
    
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
    print("✓ Created mart.v_shogun_final_shipment_daily")
    
    # -------------------------------------------------------------------------
    # 3. 統合ビュー
    # -------------------------------------------------------------------------
    
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
    print("✓ Created mart.v_csv_calendar_daily (UNION of all calendar views)")
    
    print("[mart] ✓ CSV calendar daily views created successfully")


def downgrade() -> None:
    """
    日次集計ビューを削除
    """
    op.execute("DROP VIEW IF EXISTS mart.v_csv_calendar_daily;")
    op.execute("DROP VIEW IF EXISTS mart.v_shogun_final_shipment_daily;")
    op.execute("DROP VIEW IF EXISTS mart.v_shogun_final_yard_daily;")
    op.execute("DROP VIEW IF EXISTS mart.v_shogun_final_receive_daily;")
    op.execute("DROP VIEW IF EXISTS mart.v_shogun_flash_shipment_daily;")
    op.execute("DROP VIEW IF EXISTS mart.v_shogun_flash_yard_daily;")
    op.execute("DROP VIEW IF EXISTS mart.v_shogun_flash_receive_daily;")
    print("✓ Dropped all CSV calendar daily views")
