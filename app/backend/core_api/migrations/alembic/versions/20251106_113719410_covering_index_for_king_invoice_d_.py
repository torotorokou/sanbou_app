"""covering index for KING: (invoice_d, invoice_no) INCLUDE (net_weight_detail, amount)

Revision ID: 20251106_113719410
Revises: 20251105_174743743
Create Date: 2025-11-06 02:37:20.540958

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251106_113719410'
down_revision = '20251105_174743743'
branch_labels = None
depends_on = None


# 既存の旧インデックス名（あなたの環境で作っていたもの）
OLD_IDX = "idx_king_invdate_func_no_filtered"
# 新しく作る「カバリング」インデックス名
NEW_IDX = "idx_king_invdate_receiveno_cover"

# invoice_d と同一の式（stg側の定義と一致させる）
INVOICE_D_EXPR = """
make_date(
  (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 1))::integer,
  (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer,
  (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer
)
""".strip()

# 既存の部分条件（既に運用しているフィルタを踏襲）
PARTIAL_WHERE = """
(vehicle_type_code = 1)
AND (net_weight_detail <> 0)
AND ((invoice_date)::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$')
AND ((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer BETWEEN 1 AND 12)
AND ((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer BETWEEN 1 AND 31)
""".strip()

def upgrade() -> None:
    bind = op.get_bind()
    rel = "raw.receive_king_final"
    exists = bind.execute(sa.text("SELECT to_regclass(:r)"), {"r": rel}).scalar()
    if exists is None:
        with op.get_context().autocommit_block():
            op.execute(sa.text("DO $$ BEGIN RAISE NOTICE 'skip: % not found'; END $$;"), {"r": rel})
        return

    # 1) 新しい「カバリング」インデックスを CONCURRENTLY で作成
    create_new = f"""
    CREATE INDEX CONCURRENTLY IF NOT EXISTS {NEW_IDX}
    ON {rel} (
      {INVOICE_D_EXPR},
      invoice_no
    )
    INCLUDE (net_weight_detail, amount)
    WHERE {PARTIAL_WHERE};
    """
    with op.get_context().autocommit_block():
        op.execute(sa.text(create_new))
        op.execute(sa.text(f"ANALYZE {rel};"))

    # 2) 旧インデックスがあるなら CONCURRENTLY で削除（任意：残して観察でもOK）
    with op.get_context().autocommit_block():
        op.execute(sa.text(f"DROP INDEX CONCURRENTLY IF EXISTS {OLD_IDX};"))

def downgrade() -> None:
    rel = "raw.receive_king_final"
    # 1) 旧インデックスを復元
    recreate_old = f"""
    CREATE INDEX CONCURRENTLY IF NOT EXISTS {OLD_IDX}
    ON {rel} (
      {INVOICE_D_EXPR},
      invoice_no
    )
    WHERE {PARTIAL_WHERE};
    """
    with op.get_context().autocommit_block():
        op.execute(sa.text(recreate_old))
        op.execute(sa.text(f"ANALYZE {rel};"))

    # 2) 新インデックスを削除
    with op.get_context().autocommit_block():
        op.execute(sa.text(f"DROP INDEX CONCURRENTLY IF EXISTS {NEW_IDX};"))