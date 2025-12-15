"""change_stg_columns_to_int

Revision ID: 20251128_160819394
Revises: 20251127_140000000
Create Date: 2025-11-28 07:08:20.328688

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251128_160819394'
down_revision = '20251127_140000000'
branch_labels = None
depends_on = None

# View definitions
v_active_shogun_final_shipment = """
CREATE OR REPLACE VIEW stg.v_active_shogun_final_shipment AS
 SELECT id,
    slip_date,
    client_name,
    item_name,
    net_weight,
    quantity,
    unit_name,
    unit_price,
    amount,
    transport_vendor_name,
    vendor_cd,
    vendor_name,
    site_cd,
    site_name,
    slip_type_name,
    shipment_no,
    detail_note,
    category_cd,
    category_name,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_final_shipment
  WHERE is_deleted = false;
"""

v_active_shogun_flash_shipment = """
CREATE OR REPLACE VIEW stg.v_active_shogun_flash_shipment AS
 SELECT id,
    slip_date,
    client_name,
    item_name,
    net_weight,
    quantity,
    unit_name,
    unit_price,
    amount,
    transport_vendor_name,
    vendor_cd,
    vendor_name,
    site_cd,
    site_name,
    slip_type_name,
    shipment_no,
    detail_note,
    category_cd,
    category_name,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_flash_shipment
  WHERE is_deleted = false;
"""

v_active_shogun_final_yard = """
CREATE OR REPLACE VIEW stg.v_active_shogun_final_yard AS
 SELECT id,
    slip_date,
    client_name,
    item_name,
    net_weight,
    quantity,
    unit_name,
    unit_price,
    amount,
    sales_staff_name,
    vendor_cd,
    vendor_name,
    category_cd,
    category_name,
    item_cd,
    slip_no,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_final_yard
  WHERE is_deleted = false;
"""

v_active_shogun_flash_yard = """
CREATE OR REPLACE VIEW stg.v_active_shogun_flash_yard AS
 SELECT id,
    slip_date,
    client_name,
    item_name,
    net_weight,
    quantity,
    unit_name,
    unit_price,
    amount,
    sales_staff_name,
    vendor_cd,
    vendor_name,
    category_cd,
    category_name,
    item_cd,
    slip_no,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_flash_yard
  WHERE is_deleted = false;
"""

def upgrade() -> None:
    # Drop views
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_final_shipment")
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_flash_shipment")
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_final_yard")
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_flash_yard")

    # Alter columns
    op.alter_column('shogun_final_shipment', 'shipment_no',
               existing_type=sa.Text(),
               type_=sa.Integer(),
               postgresql_using='shipment_no::integer',
               schema='stg')
    op.alter_column('shogun_flash_shipment', 'shipment_no',
               existing_type=sa.Text(),
               type_=sa.Integer(),
               postgresql_using='shipment_no::integer',
               schema='stg')
    op.alter_column('shogun_final_yard', 'slip_no',
               existing_type=sa.Text(),
               type_=sa.Integer(),
               postgresql_using='slip_no::integer',
               schema='stg')
    op.alter_column('shogun_flash_yard', 'slip_no',
               existing_type=sa.Text(),
               type_=sa.Integer(),
               postgresql_using='slip_no::integer',
               schema='stg')

    # Recreate views
    op.execute(v_active_shogun_final_shipment)
    op.execute(v_active_shogun_flash_shipment)
    op.execute(v_active_shogun_final_yard)
    op.execute(v_active_shogun_flash_yard)


def downgrade() -> None:
    # Drop views
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_final_shipment")
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_flash_shipment")
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_final_yard")
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_flash_yard")

    # Revert columns
    op.alter_column('shogun_final_shipment', 'shipment_no',
               existing_type=sa.Integer(),
               type_=sa.Text(),
               schema='stg')
    op.alter_column('shogun_flash_shipment', 'shipment_no',
               existing_type=sa.Integer(),
               type_=sa.Text(),
               schema='stg')
    op.alter_column('shogun_final_yard', 'slip_no',
               existing_type=sa.Integer(),
               type_=sa.Text(),
               schema='stg')
    op.alter_column('shogun_flash_yard', 'slip_no',
               existing_type=sa.Integer(),
               type_=sa.Text(),
               schema='stg')

    # Recreate views
    op.execute(v_active_shogun_final_shipment)
    op.execute(v_active_shogun_flash_shipment)
    op.execute(v_active_shogun_final_yard)
    op.execute(v_active_shogun_flash_yard)
