"""mart: grant select on v_receive_* to app_readonly

Revision ID: 20251105_101233931
Revises: 20251105_101107506
Create Date: 2025-11-05 01:12:34.713146

"""
from alembic import op
import sqlalchemy as sa
from alembic import context

# revision identifiers, used by Alembic.
revision = '20251105_101233931'
down_revision = '20251105_101107506'
branch_labels = None
depends_on = None
READ_ROLE = context.get_x_argument(as_dictionary=True).get("READ_ROLE", "app_readonly")

def _role_exists(name: str) -> bool:
    # オフラインでは存在確認できない
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    return bool(conn.scalar(sa.text("SELECT 1 FROM pg_roles WHERE rolname=:n"), {"n": name}))

def upgrade():
    safe_role = READ_ROLE.replace("'", "''")

    # オフライン(--sql)はコメントだけ出して終了（GRANTはオンライン環境で実行）
    if context.is_offline_mode():
        op.execute(f"-- NOTICE: Skipping grants in offline mode (target role: {safe_role})")
        return

    if _role_exists(READ_ROLE):
        op.execute(f'GRANT USAGE ON SCHEMA mart TO "{safe_role}";')
        for v in ("v_receive_daily", "v_receive_weekly", "v_receive_monthly"):
            op.execute(f'GRANT SELECT ON mart.{v} TO "{safe_role}";')
        # 以降に作成されるビュー/テーブルにも自動付与（所有者=実行ユーザ前提）
        op.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT SELECT ON TABLES TO "{safe_role}";')
    else:
        # ★ここが今回の修正点：第二引数のparamsを渡さず、文字列だけでNOTICEを出す
        op.execute(f"DO $$ BEGIN RAISE NOTICE 'Role {safe_role} does not exist; skipping grants'; END $$;")

def downgrade():
    # 非破壊ポリシーに沿って何もしない
    pass