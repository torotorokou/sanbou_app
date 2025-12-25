"""add slip_date indexes to stg.receive_shogun tables

Purpose:
  stg.receive_shogun_final と stg.receive_shogun_flash に slip_date のインデックスを追加。
  mart.v_receive_daily の GROUP BY slip_date が高速化される。

Design:
  - 部分インデックス (WHERE slip_date IS NOT NULL) でサイズ削減
  - Sequential Scan → Index Scan に変更
  - CREATE INDEX IF NOT EXISTS で冪等性を確保

Performance Impact:
  - /inbound/daily API のレスポンスタイム 20-30% 短縮を期待
  - v_receive_daily の r_shogun_final / r_shogun_flash CTE が高速化

Rollback:
  - downgrade() でインデックスを DROP

Revision ID: 20251211_100000000
Revises: 20251201_130000000
Create Date: 2025-12-11 10:00:00
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251211_100000000"
down_revision = "20251201_130000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    stg.shogun_final_receive と stg.shogun_flash_receive に slip_date のインデックスを追加

    インデックス設計:
    - 部分インデックス (WHERE slip_date IS NOT NULL) でサイズ削減
    - mart.v_receive_daily の以下のクエリを高速化:
      SELECT slip_date, sum(net_weight) / 1000.0 AS receive_ton, ...
      FROM stg.shogun_final_receive
      WHERE slip_date IS NOT NULL
      GROUP BY slip_date
    """
    print("📌 Adding slip_date indexes to stg shogun receive tables...")

    # 1. stg.shogun_final_receive に slip_date のインデックス追加
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_shogun_final_receive_slip_date
        ON stg.shogun_final_receive (slip_date)
        WHERE slip_date IS NOT NULL;
    """
    )
    print("  ✓ Created ix_shogun_final_receive_slip_date")

    # 2. stg.shogun_flash_receive に slip_date のインデックス追加
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_shogun_flash_receive_slip_date
        ON stg.shogun_flash_receive (slip_date)
        WHERE slip_date IS NOT NULL;
    """
    )
    print("  ✓ Created ix_shogun_flash_receive_slip_date")

    print("✅ Slip_date indexes added successfully")


def downgrade() -> None:
    """
    インデックスを削除
    """
    print("📌 Dropping slip_date indexes from stg shogun receive tables...")

    op.execute("DROP INDEX IF EXISTS stg.ix_shogun_flash_receive_slip_date;")
    print("  ✓ Dropped ix_shogun_flash_receive_slip_date")

    op.execute("DROP INDEX IF EXISTS stg.ix_shogun_final_receive_slip_date;")
    print("  ✓ Dropped ix_shogun_final_receive_slip_date")

    print("✅ Slip_date indexes dropped successfully")
