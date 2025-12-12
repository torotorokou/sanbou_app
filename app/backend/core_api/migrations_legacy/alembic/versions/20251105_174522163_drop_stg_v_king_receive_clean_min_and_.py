"""drop stg.v_king_receive_clean_min and legacy

Revision ID: 20251105_174522163
Revises: 20251105_174420334
Create Date: 2025-11-05 08:45:22.876835

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251105_174522163'
down_revision = '20251105_174420334'
branch_labels = None
depends_on = None

def upgrade():
    with op.get_context().autocommit_block():
        op.execute(sa.text("DROP VIEW IF EXISTS stg.v_king_receive_clean_min;"))


def downgrade():
    # 簡易復元：_min は SQL を再掲、legacy は no-op（任意で復元可）
    with op.get_context().autocommit_block():
        op.execute(sa.text("""
        CREATE OR REPLACE VIEW stg.v_king_receive_clean_min AS
        SELECT
          make_date(
            split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 1)::int,
            split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 2)::int,
            split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 3)::int
          ) AS invoice_d,
          k.invoice_no,
          k.net_weight_detail,
          k.amount
        FROM raw.receive_king_final k
        WHERE
          k.vehicle_type_code = 1
          AND k.net_weight_detail <> 0
          AND k.invoice_date::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'
          AND split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 2)::int BETWEEN 1 AND 12
          AND split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 3)::int BETWEEN 1 AND 31;
        """))
        op.execute(sa.text("GRANT SELECT ON stg.v_king_receive_clean_min TO myuser;"))