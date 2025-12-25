"""update views and indexes to reference stg schema

このマイグレーションは、テーブルが raw → stg に移動した後に、
それらを参照しているビューとインデックスを更新します。

対象:
- stg.v_king_receive_clean (raw.receive_king_final → stg.receive_king_final)
- インデックス (raw.receive_king_final → stg.receive_king_final)

Revision ID: 20251113_151137000
Revises: 20251113_150255000
Create Date: 2025-11-13 15:11:37.000000
"""

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision = "20251113_151137000"
down_revision = "20251113_150255000"
branch_labels = None
depends_on = None


def _view_exists(schema: str, view: str) -> bool:
    """ビューが存在するかチェック"""
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    qualified = f"{schema}.{view}"
    result = conn.scalar(sa.text("SELECT to_regclass(:q) IS NOT NULL"), {"q": qualified})
    return bool(result)


def upgrade():
    """
    stg スキーマのビューを更新して stg.receive_king_final を参照するようにする
    """

    # 1. stg.v_king_receive_clean の更新
    if _view_exists("stg", "v_king_receive_clean"):
        op.execute(
            """
            CREATE OR REPLACE VIEW stg.v_king_receive_clean AS
            SELECT
              make_date(
                split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 1)::int,
                split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 2)::int,
                split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 3)::int
              ) AS invoice_d,
              k.invoice_no,
              k.net_weight_detail,
              k.amount
            FROM stg.receive_king_final k
            WHERE
              k.vehicle_type_code = 1
              AND k.net_weight_detail <> 0
              AND k.invoice_date::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'
              AND split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 2)::int BETWEEN 1 AND 12
              AND split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 3)::int BETWEEN 1 AND 31;
        """
        )
        print("✓ Updated stg.v_king_receive_clean to reference stg.receive_king_final")

    # 2. インデックスの再作成（stg スキーマのテーブルに対して）
    # 既存のインデックスが raw スキーマのテーブルに対して作成されている場合は削除して再作成

    # idx_king_invdate_func_no_filtered
    op.execute("DROP INDEX IF EXISTS idx_king_invdate_func_no_filtered;")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_king_invdate_func_no_filtered
        ON stg.receive_king_final (
          make_date(
            split_part(replace(invoice_date,'/','-'), '-', 1)::int,
            split_part(replace(invoice_date,'/','-'), '-', 2)::int,
            split_part(replace(invoice_date,'/','-'), '-', 3)::int
          ),
          invoice_no
        )
        WHERE vehicle_type_code = 1
          AND net_weight_detail <> 0
          AND invoice_date ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'
          AND split_part(replace(invoice_date,'/','-'), '-', 2)::int BETWEEN 1 AND 12
          AND split_part(replace(invoice_date,'/','-'), '-', 3)::int BETWEEN 1 AND 31;
    """
    )
    print("✓ Recreated idx_king_invdate_func_no_filtered on stg.receive_king_final")

    # idx_king_invdate_receiveno_cover (covering index)
    op.execute("DROP INDEX IF EXISTS idx_king_invdate_receiveno_cover;")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_king_invdate_receiveno_cover
        ON stg.receive_king_final (
          make_date(
            (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 1))::integer,
            (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer,
            (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer
          ),
          invoice_no
        )
        INCLUDE (net_weight_detail, amount)
        WHERE (vehicle_type_code = 1)
          AND (net_weight_detail <> 0)
          AND ((invoice_date)::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$')
          AND ((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer BETWEEN 1 AND 12)
          AND ((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer BETWEEN 1 AND 31);
    """
    )
    print("✓ Recreated idx_king_invdate_receiveno_cover on stg.receive_king_final")


def downgrade():
    """
    ビューとインデックスを raw スキーマ参照に戻す
    """

    # 1. stg.v_king_receive_clean を raw 参照に戻す
    if _view_exists("stg", "v_king_receive_clean"):
        op.execute(
            """
            CREATE OR REPLACE VIEW stg.v_king_receive_clean AS
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
        """
        )

    # 2. インデックスを raw スキーマに戻す
    op.execute("DROP INDEX IF EXISTS idx_king_invdate_func_no_filtered;")
    op.execute("DROP INDEX IF EXISTS idx_king_invdate_receiveno_cover;")
    # raw スキーマのインデックスは既存のマイグレーションで作成されているので、ここでは削除のみ
