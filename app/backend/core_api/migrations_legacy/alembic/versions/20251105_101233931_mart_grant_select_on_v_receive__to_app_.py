"""mart: grant select on v_receive_* to app_readonly

Revision ID: 20251105_101233931
Revises: 20251105_101107506
Create Date: 2025-11-05 01:12:34.713146

"""

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision = "20251105_101233931"
down_revision = "20251105_101107506"
branch_labels = None
depends_on = None


def _get_read_role() -> str:
    """Get READ_ROLE from config, safe to call at runtime (not at module import)."""
    return context.get_x_argument(as_dictionary=True).get("READ_ROLE", "app_readonly")


def _role_exists(conn, name: str) -> bool:
    """Check if a PostgreSQL role exists."""
    return bool(
        conn.scalar(sa.text("SELECT 1 FROM pg_roles WHERE rolname=:n"), {"n": name})
    )


def upgrade():
    read_role = _get_read_role()
    # シングルクォート・ダブルクォートをエスケープ（PostgreSQL識別子は""でクォート、SQL文字列は''でエスケープ）
    safe_role_ident = read_role.replace('"', '""')  # 識別子用
    safe_role_str = read_role.replace("'", "''")  # 文字列用

    # オフライン(--sql)はコメントだけ出して終了（GRANTはオンライン環境で実行）
    if context.is_offline_mode():
        op.execute(
            f"-- NOTICE: Skipping grants in offline mode (target role: {safe_role_str})"
        )
        return

    conn = op.get_bind()
    if _role_exists(conn, read_role):
        op.execute(f'GRANT USAGE ON SCHEMA mart TO "{safe_role_ident}";')
        for v in ("v_receive_daily", "v_receive_weekly", "v_receive_monthly"):
            op.execute(f'GRANT SELECT ON mart.{v} TO "{safe_role_ident}";')
        # 以降に作成されるビュー/テーブルにも自動付与（所有者=実行ユーザ前提）
        op.execute(
            f'ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT SELECT ON TABLES TO "{safe_role_ident}";'
        )
    else:
        # ロールが存在しない場合はNOTICEを出力
        op.execute(
            f"DO $$ BEGIN RAISE NOTICE 'Role {safe_role_str} does not exist; skipping grants'; END $$;"
        )


def downgrade():
    # 非破壊ポリシーに沿って何もしない
    pass
