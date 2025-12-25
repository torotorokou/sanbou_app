"""mart: drop legacy wrapper views receive_* if no deps

Revision ID: 20251105_152407663
Revises: 20251105_115452784
Create Date: 2025-11-05
"""

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision = "20251105_152407663"
down_revision = "20251105_115452784"
branch_labels = None
depends_on = None

_CHECK_SQL = sa.text(
    """
WITH targets AS (
  SELECT 'receive_daily'   AS rel UNION ALL
  SELECT 'receive_weekly'  UNION ALL
  SELECT 'receive_monthly'
)
SELECT count(*) AS cnt
FROM pg_depend d
JOIN pg_rewrite r     ON r.oid = d.objid
JOIN pg_class   dep   ON r.ev_class = dep.oid    AND dep.relkind = 'v'
JOIN pg_class   src   ON d.refobjid = src.oid
JOIN pg_namespace src_ns ON src_ns.oid = src.relnamespace
JOIN targets t ON t.rel = src.relname
WHERE src_ns.nspname = 'mart';
"""
)


def _has_deps(conn) -> bool:
    cnt = conn.execute(_CHECK_SQL).scalar()
    return (cnt or 0) > 0


def upgrade():
    # オフライン(--sql)生成時: DROP 文だけを出力
    if context.is_offline_mode():
        op.execute("DROP VIEW IF EXISTS mart.receive_daily;")
        op.execute("DROP VIEW IF EXISTS mart.receive_weekly;")
        op.execute("DROP VIEW IF EXISTS mart.receive_monthly;")
        return

    # オンライン適用時: 依存があればスキップ（NOTICE）
    conn = op.get_bind()
    if _has_deps(conn):
        op.execute(
            "DO $$ BEGIN RAISE NOTICE 'mart.receive_* has dependencies; skipping drop'; END $$;"
        )
        return

    op.execute("DROP VIEW IF EXISTS mart.receive_daily;")
    op.execute("DROP VIEW IF EXISTS mart.receive_weekly;")
    op.execute("DROP VIEW IF EXISTS mart.receive_monthly;")


def downgrade():
    # 非破壊ポリシー: 復旧用の簡易ラッパー（v_ に依存）
    op.execute("CREATE OR REPLACE VIEW mart.receive_daily   AS SELECT * FROM mart.v_receive_daily;")
    op.execute(
        "CREATE OR REPLACE VIEW mart.receive_weekly  AS SELECT * FROM mart.v_receive_weekly;"
    )
    op.execute(
        "CREATE OR REPLACE VIEW mart.receive_monthly AS SELECT * FROM mart.v_receive_monthly;"
    )
