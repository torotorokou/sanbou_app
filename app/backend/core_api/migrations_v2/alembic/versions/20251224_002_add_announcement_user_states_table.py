"""add_announcement_user_states_table

Revision ID: 20251224_002
Revises: 20251224_001
Create Date: 2025-12-24

Phase 2: app.announcement_user_states テーブル追加

目的：
  ユーザーごとのお知らせ既読・確認状態を管理
  フロントエンドのlocalStorage実装をDB永続化に移行

テーブル仕様：
  - PK: id (SERIAL)
  - user_id: text not null (ユーザー識別子)
  - announcement_id: int not null -> app.announcements(id) FK
  - read_at: timestamptz (既読日時、NULL=未読)
  - ack_at: timestamptz (確認日時、NULL=未確認、criticalお知らせ用)
  - UQ: (user_id, announcement_id) で1ユーザー1お知らせ1レコードを保証

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251224_002'
down_revision = '20251224_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """app.announcement_user_states テーブルを作成"""
    
    op.execute("""
        CREATE TABLE app.announcement_user_states (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            announcement_id INTEGER NOT NULL,
            read_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
            ack_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_announcement
                FOREIGN KEY (announcement_id) 
                REFERENCES app.announcements(id) 
                ON DELETE CASCADE,
            CONSTRAINT uq_user_announcement 
                UNIQUE (user_id, announcement_id)
        );
    """)
    
    # インデックス追加
    op.execute("""
        CREATE INDEX idx_announcement_user_states_user_id 
        ON app.announcement_user_states (user_id);
    """)
    
    op.execute("""
        CREATE INDEX idx_announcement_user_states_announcement_id 
        ON app.announcement_user_states (announcement_id);
    """)
    
    # コメント追加
    op.execute("""
        COMMENT ON TABLE app.announcement_user_states IS 
        'ユーザーごとのお知らせ既読・確認状態を管理';
    """)
    op.execute("COMMENT ON COLUMN app.announcement_user_states.id IS '状態ID（PK）';")
    op.execute("COMMENT ON COLUMN app.announcement_user_states.user_id IS 'ユーザー識別子';")
    op.execute("COMMENT ON COLUMN app.announcement_user_states.announcement_id IS 'お知らせID（FK）';")
    op.execute("COMMENT ON COLUMN app.announcement_user_states.read_at IS '既読日時（NULL=未読）';")
    op.execute("COMMENT ON COLUMN app.announcement_user_states.ack_at IS '確認日時（NULL=未確認、criticalお知らせ用）';")


def downgrade() -> None:
    """app.announcement_user_states テーブルを削除"""
    op.execute("DROP TABLE IF EXISTS app.announcement_user_states CASCADE;")
