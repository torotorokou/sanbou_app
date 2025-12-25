"""raw: add receive_king_final (py, safe)

- 既存DBにテーブルがある場合は何もしない（_exists ガード）。
- 新規環境ブート時のみ CREATE。
- 既存の実DBの型に合わせ、可変長文字は Text、real は dialect の REAL、bigint は BigInteger を採用。
- このテーブルは既存状況ではPK/UK/Index/FKなし（必要になれば別リビジョンで追加）。

Revision ID: 20251105_091950593
Revises: 20251105_091848960
Create Date: 2025-11-05 09:19:50.000000
"""

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "20251105_091950593"
down_revision = "20251105_091848960"
branch_labels = None
depends_on = None


def _exists(qualified: str) -> bool:
    """テーブル存在チェック。--sql(オフライン)時は False を返し、DDLを常に出力。"""
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    return bool(
        conn.scalar(sa.text("SELECT to_regclass(:q) IS NOT NULL"), {"q": qualified})
    )


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    if not _exists("raw.receive_king_final"):
        op.create_table(
            "receive_king_final",
            # --- integer / bigint / text / real(=pg.REAL) ---
            sa.Column("invoice_no", sa.Integer(), nullable=True),
            sa.Column("invoice_date", sa.Text(), nullable=True),
            sa.Column("weighing_location_code", sa.Integer(), nullable=True),
            sa.Column("weighing_location", sa.Text(), nullable=True),
            sa.Column("sales_purchase_type_code", sa.Integer(), nullable=True),
            sa.Column("sales_purchase_type", sa.Text(), nullable=True),
            sa.Column("document_type_code", sa.Integer(), nullable=True),
            sa.Column("document_type", sa.Text(), nullable=True),
            sa.Column("delivery_no", sa.BigInteger(), nullable=True),
            sa.Column("vehicle_type_code", sa.Integer(), nullable=True),
            sa.Column("vehicle_type", sa.Text(), nullable=True),
            sa.Column("customer_code", sa.Integer(), nullable=True),
            sa.Column("customer", sa.Text(), nullable=True),
            sa.Column("site_code", sa.Integer(), nullable=True),
            sa.Column("site", sa.Text(), nullable=True),
            sa.Column("discharge_company_code", sa.Integer(), nullable=True),
            sa.Column("discharge_company", sa.Text(), nullable=True),
            sa.Column("discharge_site_code", sa.Integer(), nullable=True),
            sa.Column("discharge_site", sa.Text(), nullable=True),
            sa.Column("carrier_code", sa.Integer(), nullable=True),
            sa.Column("carrier", sa.Text(), nullable=True),
            sa.Column("disposal_company_code", sa.Integer(), nullable=True),
            sa.Column("disposal_contractor", sa.Text(), nullable=True),
            sa.Column("disposal_site_code", sa.Integer(), nullable=True),
            sa.Column("disposal_site", sa.Text(), nullable=True),
            sa.Column("gross_weight", sa.Integer(), nullable=True),
            sa.Column("tare_weight", sa.Integer(), nullable=True),
            sa.Column("adjusted_weight", sa.Integer(), nullable=True),
            sa.Column("net_weight", sa.Integer(), nullable=True),
            sa.Column("counterparty_measured_weight", sa.Integer(), nullable=True),
            sa.Column("observed_quantity", pg.REAL(), nullable=True),
            sa.Column("weighing_time_gross", sa.Text(), nullable=True),
            sa.Column("weighing_time_tare", sa.Text(), nullable=True),
            sa.Column("weighing_location_code1", sa.Integer(), nullable=True),
            sa.Column("weighing_location1", sa.Text(), nullable=True),
            sa.Column("vehicle_no", sa.Integer(), nullable=True),
            sa.Column("vehicle_kind", sa.Text(), nullable=True),
            sa.Column("driver", sa.Text(), nullable=True),
            sa.Column("sales_person_code", sa.Integer(), nullable=True),
            sa.Column("sales_person", sa.Text(), nullable=True),
            sa.Column("admin_person_code", sa.Integer(), nullable=True),
            sa.Column("admin_person", sa.Text(), nullable=True),
            sa.Column("sales_amount", sa.Integer(), nullable=True),
            sa.Column("sales_tax", sa.Integer(), nullable=True),
            sa.Column("purchase_amount", sa.Integer(), nullable=True),
            sa.Column("purchase_tax", sa.Integer(), nullable=True),
            sa.Column("aggregate_ton", pg.REAL(), nullable=True),
            sa.Column("aggregate_kg", sa.Integer(), nullable=True),
            sa.Column("aggregate_m3", pg.REAL(), nullable=True),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("item_category_code", sa.Integer(), nullable=True),
            sa.Column("item_category", sa.Text(), nullable=True),
            sa.Column("item_code", sa.Integer(), nullable=True),
            sa.Column("item_name", sa.Text(), nullable=True),
            sa.Column("quantity", pg.REAL(), nullable=True),
            sa.Column("unit_code", sa.Integer(), nullable=True),
            sa.Column("unit", sa.Text(), nullable=True),
            sa.Column("unit_price", pg.REAL(), nullable=True),
            sa.Column("amount", sa.Integer(), nullable=True),
            sa.Column("aggregation_type_code", sa.Integer(), nullable=True),
            sa.Column("aggregation_type", sa.Text(), nullable=True),
            sa.Column("unit_price_calc", pg.REAL(), nullable=True),
            sa.Column("amount_calc", sa.Integer(), nullable=True),
            sa.Column("tax_amount", sa.Integer(), nullable=True),
            sa.Column("gross_weight_detail", sa.Integer(), nullable=True),
            sa.Column("tare_weight_detail", sa.Integer(), nullable=True),
            sa.Column("net_weight_detail", sa.Integer(), nullable=True),
            sa.Column("scale_ratio", sa.Integer(), nullable=True),
            sa.Column("scale", sa.Integer(), nullable=True),
            sa.Column("remarks_customer", sa.Text(), nullable=True),
            sa.Column("remarks_internal", sa.Text(), nullable=True),
            sa.Column("param_start_date", sa.Text(), nullable=True),
            sa.Column("param_end_date", sa.Text(), nullable=True),
            sa.Column("param_sales_purchase_type", sa.Text(), nullable=True),
            sa.Column("param_vehicle_type", sa.Text(), nullable=True),
            sa.Column("param_document_type", sa.Text(), nullable=True),
            sa.Column("param_admin_person", sa.Text(), nullable=True),
            sa.Column("param_company_name", sa.Text(), nullable=True),
            sa.Column("param_weighing_place_name", sa.Text(), nullable=True),
            sa.Column("quantity_ton", pg.REAL(), nullable=True),
            sa.Column("quantity_kg", pg.REAL(), nullable=True),
            sa.Column("quantity_m3", pg.REAL(), nullable=True),
            sa.Column("amount_on_account", sa.Integer(), nullable=True),
            sa.Column("amount_cash", sa.Integer(), nullable=True),
            sa.Column("tax_on_account", sa.Integer(), nullable=True),
            sa.Column("tax_cash", sa.Integer(), nullable=True),
            schema="raw",
        )
    # 既存DBでは _exists True のため何も起きない想定


def downgrade():
    # 非破壊運用のため DROP は行わない
    pass
