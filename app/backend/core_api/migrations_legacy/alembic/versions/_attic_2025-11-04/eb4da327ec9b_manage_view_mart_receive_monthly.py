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
    """-x READ_ROLE=... があればそれを使い、無ければ既定 app_readonly。"""
    try:
        x = context.get_x_argument(as_dictionary=True)
        if isinstance(x, dict) and x.get("READ_ROLE"):
            return x["READ_ROLE"]
    except Exception:
        pass
    return "app_readonly"


def _qi(ident: str) -> str:
    """Postgres識別子を安全に二重引用。"""
    return '"' + ident.replace('"', '""') + '"'


def _role_exists(bind, name: str) -> bool:
    row = bind.execute(
        sa.text("SELECT 1 FROM pg_roles WHERE rolname = :n"),
        {"n": name},
    ).fetchone()
    return bool(row)


def upgrade():
    role = _get_read_role()

    # オフライン(--sql)はコメントだけ出力
    if context.is_offline_mode():
        op.execute(f"-- NOTICE: skipping GRANTs in offline mode (target role: {role})")
        return

    bind = op.get_bind()
    if _role_exists(bind, role):
        qrole = _qi(role)

        # schema usage（view参照に必要）
        op.execute(f"GRANT USAGE ON SCHEMA mart TO {qrole};")

        # 明示ビューに付与
        for v in (
            "mart.v_receive_daily",
            "mart.v_receive_weekly",
            "mart.v_receive_monthly",
        ):
            op.execute(f"GRANT SELECT ON {v} TO {qrole};")

        # 以後 mart スキーマで作成されるテーブル/ビューにも自動付与
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT SELECT ON TABLES TO {qrole};"
        )
    else:
        # 役割が無い環境ではNOTICEだけ出して安全にスキップ
        role_lit = role.replace("'", "''")
        op.execute(
            f"DO $$ BEGIN RAISE NOTICE 'Role % does not exist; skipping grants', '{role_lit}'; END $$;"
        )


def downgrade():
    # ベストエフォートで取り消し（役割が無ければ何もしない）
    if context.is_offline_mode():
        op.execute("-- NOTICE: skipping REVOKE in offline mode")
        return

    role = _get_read_role()
    bind = op.get_bind()
    if _role_exists(bind, role):
        qrole = _qi(role)
        for v in (
            "mart.v_receive_daily",
            "mart.v_receive_weekly",
            "mart.v_receive_monthly",
        ):
            op.execute(f"REVOKE SELECT ON {v} FROM {qrole};")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA mart REVOKE SELECT ON TABLES FROM {qrole};"
        )
