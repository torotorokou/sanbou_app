"""kpi tables: monthly_targets baseline (safe)

Revision ID: 20251104_174818076
Revises: 20251104_210000000
Create Date: 2025-11-04 08:48:18.834992

"""
from alembic import op
import sqlalchemy as sa
from alembic import context


# revision identifiers, used by Alembic.
revision = '20251104_174818076'
down_revision = '20251104_210000000'
branch_labels = None
depends_on = None



def _exists(qualified: str) -> bool:
    """
    Returns True if the schema-qualified table exists.
    In offline (--sql) mode, always returns False to emit DDL for bootstrap SQL.
    """
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    return bool(
        conn.execute(sa.text("SELECT to_regclass(:q) IS NOT NULL"), {"q": qualified}).scalar()
    )

def upgrade():
    """
    kpi.monthly_targets を既存DBに影響なく管理下へ。
    既存DB: _exists=True のため no-op（DDL未実行）
    新規DB: テーブルと索引を作成
    """
    # スキーマが無ければ作る（複数回実行しても安全）
    op.execute("CREATE SCHEMA IF NOT EXISTS kpi;")

    # 既に存在する環境では何もしない（安全）
    if not _exists("kpi.monthly_targets"):
        op.create_table(
            "monthly_targets",
            sa.Column("month_date", sa.Date(), nullable=False),
            sa.Column("segment", sa.Text(), nullable=False),
            sa.Column("metric", sa.Text(), nullable=False),
            # 実DBに合わせて精度固定
            sa.Column("value", sa.Numeric(20, 4), nullable=False),
            sa.Column("unit", sa.Text(), nullable=False),
            sa.Column("label", sa.Text(), nullable=True),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("note", sa.Text(), nullable=True),

            # 制約名は実DBと完全一致させる
            sa.UniqueConstraint("month_date", "segment", "metric", name="uq_monthly_targets"),
            sa.CheckConstraint(
                # 実DBのCHECK式（timestamptz を介した月初判定）に合わせる
                "month_date = date_trunc('month', month_date::timestamptz)::date",
                name="chk_month_is_first",
            ),
            sa.ForeignKeyConstraint(
                ["month_date"],
                ["ref.calendar_month.month_date"],
                name="fk_kpi_month",
            ),
            schema="kpi",
        )

        # インデックス（名称も実DBと一致）
        op.create_index(
            "idx_kpi_month_date",
            "monthly_targets",
            ["month_date"],
            unique=False,
            schema="kpi",
        )



def downgrade():
    # drop index then table (reverse order)
    op.drop_index("idx_kpi_month_date", table_name="monthly_targets", schema="kpi")
    op.drop_table("monthly_targets", schema="kpi")