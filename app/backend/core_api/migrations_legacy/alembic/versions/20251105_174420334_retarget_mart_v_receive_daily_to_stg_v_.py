"""retarget mart.v_receive_daily to stg.v_king_receive_clean

Revision ID: 20251105_174420334
Revises: 20251105_174329122
Create Date: 2025-11-05 08:44:24.662582

"""

import re

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251105_174420334"
down_revision = "20251105_174329122"
branch_labels = None
depends_on = None


def _swap_min_to_clean(sql: str) -> str:
    # 素直な置換（クオート/余白差異も想定して緩めに）
    return re.sub(
        r"stg\.v_king_receive_clean_min\b", "stg.v_king_receive_clean", sql, flags=re.I
    )


def upgrade():
    bind = op.get_bind()
    view_sql = bind.execute(
        sa.text("SELECT pg_get_viewdef('mart.v_receive_daily'::regclass, true)")
    ).scalar()
    if not view_sql:
        raise RuntimeError("could not fetch mart.v_receive_daily")

    new_sql = _swap_min_to_clean(view_sql)
    if new_sql == view_sql:
        # 既に置換済みならそのまま
        return

    with op.get_context().autocommit_block():
        op.execute(
            sa.text(f"CREATE OR REPLACE VIEW mart.v_receive_daily AS {new_sql};")
        )


def downgrade():
    # 逆方向（clean -> _min）置換
    bind = op.get_bind()
    view_sql = bind.execute(
        sa.text("SELECT pg_get_viewdef('mart.v_receive_daily'::regclass, true)")
    ).scalar()
    if not view_sql:
        return
    back_sql = re.sub(
        r"stg\.v_king_receive_clean\b",
        "stg.v_king_receive_clean_min",
        view_sql,
        flags=re.I,
    )

    with op.get_context().autocommit_block():
        op.execute(
            sa.text(f"CREATE OR REPLACE VIEW mart.v_receive_daily AS {back_sql};")
        )
