"""index receive_king_final for v_target_card_per_day

Revision ID: 20251105_160859083
Revises: 20251105_160031021
Create Date: 2025-11-05 07:08:59.817904

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251105_160859083"
down_revision = "20251105_160031021"
branch_labels = None
depends_on = None

TARGET_REL = "raw.receive_king_final"


def upgrade():
    bind = op.get_bind()
    exists = bind.execute(sa.text(f"SELECT to_regclass('{TARGET_REL}')")).scalar()
    if exists is None:
        with op.get_context().autocommit_block():
            op.execute(sa.text(f"DO $$ BEGIN RAISE NOTICE 'skip: {TARGET_REL} not found'; END $$;"))
        return

    # IMMUTABLE な式: make_date(split_part(replace(...)))
    with op.get_context().autocommit_block():
        op.execute(
            sa.text(
                f"""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_king_invdate_func_no_filtered
            ON {TARGET_REL} (
              make_date(
                split_part(replace(invoice_date,'/','-'), '-', 1)::int,
                split_part(replace(invoice_date,'/','-'), '-', 2)::int,
                split_part(replace(invoice_date,'/','-'), '-', 3)::int
              ),
              invoice_no
            )
            WHERE vehicle_type_code = 1
              AND net_weight_detail <> 0
              AND invoice_date ~ '^[0-9]{{4}}[-/][0-9]{{2}}[-/][0-9]{{2}}$'
              AND split_part(replace(invoice_date,'/','-'), '-', 2)::int BETWEEN 1 AND 12
              AND split_part(replace(invoice_date,'/','-'), '-', 3)::int BETWEEN 1 AND 31;
        """
            )
        )
        op.execute(sa.text(f"ANALYZE {TARGET_REL};"))


def downgrade():
    with op.get_context().autocommit_block():
        op.execute(sa.text("DROP INDEX IF EXISTS idx_king_invdate_func_no_filtered;"))
