"""shrink king-clean view by creating a minimal view and repoint v_receive_daily

Revision ID: 20251105_172835295
Revises: 20251105_171336072
Create Date: 2025-11-05 08:28:35
"""
from alembic import op
import sqlalchemy as sa

revision = "20251105_172835295"
down_revision = "20251105_171336072"
branch_labels = None
depends_on = None

SQL_CREATE_MIN_VIEW = """
CREATE OR REPLACE VIEW stg.v_king_receive_clean_min AS
SELECT
  -- 文字列日付→DATE（IMMUTABLE関数のみで構成）
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
"""

def upgrade():
    bind = op.get_bind()

    # 1) 軽量ビューを新規作成（既存の重いビューは触らない）
    with op.get_context().autocommit_block():
        op.execute(sa.text(SQL_CREATE_MIN_VIEW))
        op.execute(sa.text("GRANT SELECT ON stg.v_king_receive_clean_min TO myuser;"))

    # 2) mart.v_receive_daily の参照先を _min に差し替え
    vdef = bind.execute(sa.text(
        "SELECT pg_get_viewdef('mart.v_receive_daily'::regclass, true)"
    )).scalar()

    if not vdef:
        raise RuntimeError("could not fetch v_receive_daily definition")

    # 素直なテキスト置換（現行の定義にそのままマッチする想定）
    BEFORE = "FROM stg.v_king_receive_clean k"
    AFTER  = "FROM stg.v_king_receive_clean_min k"

    if BEFORE not in vdef:
        # 多少のフォーマット差異に備えてスペースを1つだけ緩めたパターンも試す
        alt_before = "FROM stg.v_king_receive_clean k".replace("  ", " ")
        if alt_before in vdef:
            vdef = vdef.replace(alt_before, AFTER)
        else:
            # 定義が想定と違う場合は内容を出して止める
            snippet = vdef[:400]
            raise RuntimeError(
                "pattern not found: 'FROM stg.v_king_receive_clean k'\n"
                f"head of viewdef:\n{snippet}"
            )
    else:
        vdef = vdef.replace(BEFORE, AFTER)

    # 再作成
    with op.get_context().autocommit_block():
        op.execute(sa.text(f"CREATE OR REPLACE VIEW mart.v_receive_daily AS {vdef};"))

def downgrade():
    bind = op.get_bind()

    # v_receive_daily を元のビュー参照に戻す
    vdef = bind.execute(sa.text(
        "SELECT pg_get_viewdef('mart.v_receive_daily'::regclass, true)"
    )).scalar()
    if vdef and "stg.v_king_receive_clean_min" in vdef:
        vdef = vdef.replace("FROM stg.v_king_receive_clean_min k", "FROM stg.v_king_receive_clean k")
        with op.get_context().autocommit_block():
            op.execute(sa.text(f"CREATE OR REPLACE VIEW mart.v_receive_daily AS {vdef};"))

    # 軽量ビューを削除
    with op.get_context().autocommit_block():
        op.execute(sa.text("DROP VIEW IF EXISTS stg.v_king_receive_clean_min;"))
