"""change stg.v_king_receive_clean

Revision ID: 20251105_165932182
Revises: 20251105_165006509
Create Date: 2025-11-05 07:59:32.956921

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251105_165932182"
down_revision = "20251105_165006509"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS stg;")
    op.execute(
        """
    CREATE OR REPLACE VIEW stg.v_king_receive_daily AS
    SELECT
      k.invoice_d                         AS ddate,
      -- kg→t 換算（kgの場合）。既にtなら /1000.0 を外す
      SUM(k.net_weight_detail)::numeric / 1000.0 AS receive_net_ton
    FROM stg.v_king_receive_clean k
    GROUP BY 1;
    """
    )
    op.execute("GRANT USAGE ON SCHEMA stg TO myuser;")
    op.execute("GRANT SELECT ON stg.v_king_receive_daily TO myuser;")


def downgrade():
    op.execute("DROP VIEW IF EXISTS stg.v_king_receive_daily;")
