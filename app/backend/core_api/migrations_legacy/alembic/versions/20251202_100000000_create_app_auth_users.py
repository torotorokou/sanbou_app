"""create app_auth.users table for authentication

このマイグレーションは認証基盤のユーザーマスタテーブルを作成します。

変更内容:
1. app_auth スキーマ作成
2. app_auth.users テーブル作成
   - 認証プロバイダ（Google OAuth2 / IAP 等）の情報を保存
   - メールアドレス、表示名、ロール（配列）を管理
   - ソフトデリート対応（is_active フラグ）
   - 最終ログイン日時のトラッキング
3. ユニーク制約
   - email: メールアドレスの一意性
   - (auth_provider, auth_subject): プロバイダごとのユーザーIDの一意性

Revision ID: 20251202_100000000
Revises: 20251201_160000000
Create Date: 2025-12-02 10:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251202_100000000"
down_revision = "20251201_160000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    app_auth スキーマと users テーブルを作成
    """
    # 1. app_auth スキーマ作成
    op.execute("CREATE SCHEMA IF NOT EXISTS app_auth;")
    op.execute("GRANT USAGE ON SCHEMA app_auth TO myuser;")

    # 2. app_auth.users テーブル作成
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="ユーザーID（主キー）",
        ),
        sa.Column(
            "auth_provider",
            sa.Text(),
            nullable=False,
            server_default="google",
            comment="認証プロバイダ（google, iap など）",
        ),
        sa.Column(
            "auth_subject",
            sa.Text(),
            nullable=False,
            comment="認証プロバイダ内のユーザー識別子（sub claim）",
        ),
        sa.Column(
            "email", sa.Text(), nullable=False, comment="メールアドレス（ログイン用）"
        ),
        sa.Column("display_name", sa.Text(), nullable=False, comment="表示名"),
        sa.Column(
            "roles",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'"),
            comment="ユーザーロール（admin, user, viewer など）",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="有効フラグ（ソフトデリート用）",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="作成日時",
        ),
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="最終ログイン日時",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint(
            "auth_provider", "auth_subject", name="uq_users_provider_subject"
        ),
        schema="app_auth",
        comment="認証ユーザーマスタ",
    )

    # 3. インデックス作成
    op.create_index(
        "ix_users_email", "users", ["email"], schema="app_auth", unique=False
    )

    op.create_index(
        "ix_users_is_active", "users", ["is_active"], schema="app_auth", unique=False
    )


def downgrade() -> None:
    """
    app_auth.users テーブルとスキーマを削除
    """
    # インデックス削除
    op.drop_index("ix_users_is_active", table_name="users", schema="app_auth")
    op.drop_index("ix_users_email", table_name="users", schema="app_auth")

    # テーブル削除
    op.drop_table("users", schema="app_auth")

    # スキーマ削除（他にテーブルがない前提）
    op.execute("DROP SCHEMA IF EXISTS app_auth CASCADE;")
