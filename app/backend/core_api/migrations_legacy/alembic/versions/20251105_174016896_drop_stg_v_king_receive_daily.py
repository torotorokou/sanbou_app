"""drop stg.v_king_receive_daily

Revision ID: 20251105_174016896
Revises: 20251105_172835295
Create Date: 2025-11-05 08:40:17.667268

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251105_174016896'
down_revision = '20251105_172835295'
branch_labels = None
depends_on = None



SQL_DROP = "DROP VIEW IF EXISTS stg.v_king_receive_daily;"

# 最小復元（必要になれば戻せる）
SQL_RECREATE = """
CREATE OR REPLACE VIEW stg.v_king_receive_daily AS
SELECT
  k.invoice_d AS ddate,
  SUM(k.net_weight_detail)::numeric/1000.0 AS receive_ton,
  COUNT(DISTINCT k.invoice_no)            AS vehicle_count,
  SUM(k.amount)::numeric                  AS sales_yen
FROM stg.v_king_receive_clean_min k
GROUP BY k.invoice_d;
"""

def upgrade():
    with op.get_context().autocommit_block():
        op.execute(sa.text(SQL_DROP))

def downgrade():
    with op.get_context().autocommit_block():
        op.execute(sa.text(SQL_RECREATE))
        op.execute(sa.text("GRANT SELECT ON stg.v_king_receive_daily TO myuser;"))