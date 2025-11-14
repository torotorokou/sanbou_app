"""add category columns to shipment tables

Revision ID: 20251114_add_shipment_category
Revises: 20251114_remove_en_suffix
Create Date: 2025-11-14

Description:
    shipment テーブルに category_cd と category_name カラムを追加。
    YAMLで定義されているがテーブルに存在しなかったカラムを追加。
    
    対象:
    - raw.shipment_shogun_flash
    - raw.shipment_shogun_final
    - stg.shipment_shogun_flash
    - stg.shipment_shogun_final
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251114_add_shipment_category'
down_revision: Union[str, None] = '20251114_remove_en_suffix'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    shipment テーブルに category_cd と category_name カラムを追加
    """
    
    # raw スキーマ (TEXT型)
    for table in ['shipment_shogun_flash', 'shipment_shogun_final']:
        op.execute(f"ALTER TABLE raw.{table} ADD COLUMN IF NOT EXISTS category_cd TEXT")
        op.execute(f"ALTER TABLE raw.{table} ADD COLUMN IF NOT EXISTS category_name TEXT")
    
    # stg スキーマ (型付き)
    for table in ['shipment_shogun_flash', 'shipment_shogun_final']:
        op.execute(f"ALTER TABLE stg.{table} ADD COLUMN IF NOT EXISTS category_cd INTEGER")
        op.execute(f"ALTER TABLE stg.{table} ADD COLUMN IF NOT EXISTS category_name VARCHAR")
    
    print("✅ Added category_cd and category_name columns to shipment tables")


def downgrade() -> None:
    """
    追加したカラムを削除
    """
    
    # raw スキーマ
    for table in ['shipment_shogun_flash', 'shipment_shogun_final']:
        op.execute(f"ALTER TABLE raw.{table} DROP COLUMN IF EXISTS category_cd")
        op.execute(f"ALTER TABLE raw.{table} DROP COLUMN IF EXISTS category_name")
    
    # stg スキーマ
    for table in ['shipment_shogun_flash', 'shipment_shogun_final']:
        op.execute(f"ALTER TABLE stg.{table} DROP COLUMN IF EXISTS category_cd")
        op.execute(f"ALTER TABLE stg.{table} DROP COLUMN IF EXISTS category_name")
    
    print("⏪ Removed category_cd and category_name columns from shipment tables")
