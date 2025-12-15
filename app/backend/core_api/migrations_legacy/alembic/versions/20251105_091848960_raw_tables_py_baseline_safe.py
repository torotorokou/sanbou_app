"""raw tables: py baseline (safe)

Revision ID: 20251105_091848960
Revises: 20251104_174818076
Create Date: 2025-11-05 00:18:49.804814

"""
from alembic import op
import sqlalchemy as sa
from alembic import context

# revision identifiers, used by Alembic.
revision = '20251105_091848960'
down_revision = '20251104_174818076'
branch_labels = None
depends_on = None


def _exists(qualified: str) -> bool:
    """
    指定のスキーマ修飾名のテーブルが存在するか。
    - --sql(オフライン)時は常に False を返す（DDLを出力するため）
    """
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    return bool(conn.scalar(sa.text("SELECT to_regclass(:q) IS NOT NULL"), {"q": qualified}))


def upgrade():
    # スキーマだけは常に存在させる（非破壊）
    op.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    # -------------------------------------------------------------------------
    # 1) raw.receive_shogun_final
    # -------------------------------------------------------------------------
    if not _exists("raw.receive_shogun_final"):
        op.create_table(
            "receive_shogun_final",
            sa.Column("slip_date", sa.Date(), nullable=True),
            sa.Column("sales_date", sa.Date(), nullable=True),
            sa.Column("payment_date", sa.Date(), nullable=True),
            sa.Column("vendor_cd", sa.Integer(), nullable=True),
            sa.Column("vendor_name", sa.Text(), nullable=True),
            sa.Column("slip_type_cd", sa.Integer(), nullable=True),
            sa.Column("slip_type_name", sa.Text(), nullable=True),
            sa.Column("item_cd", sa.Integer(), nullable=True),
            sa.Column("item_name", sa.Text(), nullable=True),
            sa.Column("net_weight", sa.Numeric(), nullable=True),
            sa.Column("quantity", sa.Numeric(), nullable=True),
            sa.Column("unit_cd", sa.Integer(), nullable=True),
            sa.Column("unit_name", sa.Text(), nullable=True),
            sa.Column("unit_price", sa.Numeric(), nullable=True),
            sa.Column("amount", sa.Numeric(), nullable=True),
            sa.Column("receive_no", sa.Integer(), nullable=True),
            sa.Column("aggregate_item_cd", sa.Integer(), nullable=True),
            sa.Column("aggregate_item_name", sa.Text(), nullable=True),
            sa.Column("category_cd", sa.Integer(), nullable=True),
            sa.Column("category_name", sa.Text(), nullable=True),
            sa.Column("weighing_time_gross", sa.Time(timezone=False), nullable=True),
            sa.Column("weighing_time_empty", sa.Time(timezone=False), nullable=True),
            sa.Column("site_cd", sa.Integer(), nullable=True),
            sa.Column("site_name", sa.Text(), nullable=True),
            sa.Column("unload_vendor_cd", sa.Integer(), nullable=True),
            sa.Column("unload_vendor_name", sa.Text(), nullable=True),
            sa.Column("unload_site_cd", sa.Integer(), nullable=True),
            sa.Column("unload_site_name", sa.Text(), nullable=True),
            sa.Column("transport_vendor_cd", sa.Integer(), nullable=True),
            sa.Column("transport_vendor_name", sa.Text(), nullable=True),
            sa.Column("client_cd", sa.Text(), nullable=True),
            sa.Column("client_name", sa.Text(), nullable=True),
            sa.Column("manifest_type_cd", sa.Integer(), nullable=True),
            sa.Column("manifest_type_name", sa.Text(), nullable=True),
            sa.Column("manifest_no", sa.Text(), nullable=True),
            sa.Column("sales_staff_cd", sa.Integer(), nullable=True),
            sa.Column("sales_staff_name", sa.Text(), nullable=True),
            sa.Column("column38", sa.Text(), nullable=True),
            sa.Column("column39", sa.Text(), nullable=True),
            schema="raw",
        )
        # FK (slip_date -> ref.calendar_day.ddate)
        op.create_foreign_key(
            "fk_shogun_final_ddate",
            "receive_shogun_final",
            "calendar_day",
            local_cols=["slip_date"],
            remote_cols=["ddate"],
            source_schema="raw",
            referent_schema="ref",
        )
        # index
        op.create_index(
            "idx_shogun_final_slip_date",
            "receive_shogun_final",
            ["slip_date"],
            unique=False,
            schema="raw",
        )

    # -------------------------------------------------------------------------
    # 2) raw.receive_shogun_flash
    # -------------------------------------------------------------------------
    if not _exists("raw.receive_shogun_flash"):
        op.create_table(
            "receive_shogun_flash",
            sa.Column("slip_date", sa.Date(), nullable=True),
            sa.Column("sales_date", sa.Date(), nullable=True),
            sa.Column("payment_date", sa.Date(), nullable=True),
            sa.Column("vendor_cd", sa.Integer(), nullable=True),
            sa.Column("vendor_name", sa.Text(), nullable=True),
            sa.Column("slip_type_cd", sa.Integer(), nullable=True),
            sa.Column("slip_type_name", sa.Text(), nullable=True),
            sa.Column("item_cd", sa.Integer(), nullable=True),
            sa.Column("item_name", sa.Text(), nullable=True),
            sa.Column("net_weight", sa.Numeric(), nullable=True),
            sa.Column("quantity", sa.Numeric(), nullable=True),
            sa.Column("unit_cd", sa.Integer(), nullable=True),
            sa.Column("unit_name", sa.Text(), nullable=True),
            sa.Column("unit_price", sa.Numeric(), nullable=True),
            sa.Column("amount", sa.Numeric(), nullable=True),
            sa.Column("receive_no", sa.Integer(), nullable=True),
            sa.Column("aggregate_item_cd", sa.Integer(), nullable=True),
            sa.Column("aggregate_item_name", sa.Text(), nullable=True),
            sa.Column("category_cd", sa.Integer(), nullable=True),
            sa.Column("category_name", sa.Text(), nullable=True),
            sa.Column("weighing_time_gross", sa.Time(timezone=False), nullable=True),
            sa.Column("weighing_time_empty", sa.Time(timezone=False), nullable=True),
            sa.Column("site_cd", sa.Integer(), nullable=True),
            sa.Column("site_name", sa.Text(), nullable=True),
            sa.Column("unload_vendor_cd", sa.Integer(), nullable=True),
            sa.Column("unload_vendor_name", sa.Text(), nullable=True),
            sa.Column("unload_site_cd", sa.Integer(), nullable=True),
            sa.Column("unload_site_name", sa.Text(), nullable=True),
            sa.Column("transport_vendor_cd", sa.Integer(), nullable=True),
            sa.Column("transport_vendor_name", sa.Text(), nullable=True),
            sa.Column("client_cd", sa.Text(), nullable=True),
            sa.Column("client_name", sa.Text(), nullable=True),
            sa.Column("manifest_type_cd", sa.Integer(), nullable=True),
            sa.Column("manifest_type_name", sa.Text(), nullable=True),
            sa.Column("manifest_no", sa.Text(), nullable=True),
            sa.Column("sales_staff_cd", sa.Integer(), nullable=True),
            sa.Column("sales_staff_name", sa.Text(), nullable=True),
            sa.Column("column38", sa.Text(), nullable=True),
            sa.Column("column39", sa.Text(), nullable=True),
            schema="raw",
        )
        op.create_foreign_key(
            "fk_shogun_flash_ddate",
            "receive_shogun_flash",
            "calendar_day",
            local_cols=["slip_date"],
            remote_cols=["ddate"],
            source_schema="raw",
            referent_schema="ref",
        )
        op.create_index(
            "idx_shogun_flash_slip_date",
            "receive_shogun_flash",
            ["slip_date"],
            unique=False,
            schema="raw",
        )

    # -------------------------------------------------------------------------
    # 3) raw.receive_king_final は別リビジョンで追加予定
    #    （列数が多いためヘルパ経由で正確に移植）
    # -------------------------------------------------------------------------


def downgrade():
    # 非破壊運用のため DROP は原則しない
    pass