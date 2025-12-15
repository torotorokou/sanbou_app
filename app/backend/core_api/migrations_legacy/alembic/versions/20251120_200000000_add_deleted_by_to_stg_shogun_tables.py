"""add deleted_by column to stg.shogun_* tables

このマイグレーションは、stg.shogun_*_* テーブルに欠けている deleted_by カラムを追加します。

背景:
- マイグレーション 20251119_130000000 で deleted_by を追加したが、
  対象テーブル名が旧命名規則 (receive_shogun_*) だった
- その後 20251120_091427843 でテーブルが shogun_*_* にリネームされた
- 結果として、現在のテーブルには deleted_by カラムが存在しない

このマイグレーションで修正:
- stg.shogun_flash_receive
- stg.shogun_flash_shipment
- stg.shogun_flash_yard
- stg.shogun_final_receive
- stg.shogun_final_shipment
- stg.shogun_final_yard

カラム仕様:
- deleted_by: text NULL (削除実行者: ユーザー名またはシステム識別子)

Revision ID: 20251120_200000000
Revises: 20251120_190000000
Create Date: 2025-11-20 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "20251120_200000000"
down_revision = "20251120_190000000"
branch_labels = None
depends_on = None


# 対象となるstg将軍テーブルのリスト (新命名規則)
STG_SHOGUN_TABLES = [
    "shogun_flash_receive",
    "shogun_flash_shipment",
    "shogun_flash_yard",
    "shogun_final_receive",
    "shogun_final_shipment",
    "shogun_final_yard",
]


def upgrade() -> None:
    """
    stg.shogun_*_* テーブルに deleted_by カラムを追加
    """
    
    print("[stg.shogun_*] Adding deleted_by column to 6 tables...")
    
    for table_name in STG_SHOGUN_TABLES:
        # deleted_by カラムが既に存在するかチェック
        conn = op.get_bind()
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_schema = 'stg' 
                  AND table_name = :table_name 
                  AND column_name = 'deleted_by'
            )
        """), {"table_name": table_name})
        
        exists = result.scalar()
        
        if not exists:
            print(f"  ✓ Adding deleted_by to stg.{table_name}")
            op.add_column(
                table_name,
                sa.Column(
                    "deleted_by",
                    sa.Text(),
                    nullable=True,
                    comment="削除実行者 (ユーザー名またはシステム識別子)"
                ),
                schema="stg"
            )
        else:
            print(f"  ⊘ stg.{table_name} already has deleted_by, skipping")
    
    print("[stg.shogun_*] deleted_by column addition completed")


def downgrade() -> None:
    """
    deleted_by カラムを削除（ロールバック用）
    """
    
    print("[stg.shogun_*] Removing deleted_by column from 6 tables...")
    
    for table_name in STG_SHOGUN_TABLES:
        conn = op.get_bind()
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_schema = 'stg' 
                  AND table_name = :table_name 
                  AND column_name = 'deleted_by'
            )
        """), {"table_name": table_name})
        
        exists = result.scalar()
        
        if exists:
            print(f"  ✓ Dropping deleted_by from stg.{table_name}")
            op.drop_column(table_name, "deleted_by", schema="stg")
        else:
            print(f"  ⊘ stg.{table_name} has no deleted_by, skipping")
    
    print("[stg.shogun_*] deleted_by column removal completed")
