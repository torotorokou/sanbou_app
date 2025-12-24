"""add_announcements_table

Revision ID: 20251224_001
Revises: 20251216_004
Create Date: 2025-12-24

Phase 1: app.announcements テーブル追加

目的：
  システムのお知らせ（アナウンスメント）を管理するテーブル
  フロントエンドのMVP実装（localStorage）をDB永続化に移行

テーブル仕様：
  - PK: id (SERIAL)
  - title: varchar(255) not null
  - body_md: text not null (Markdown形式の本文)
  - severity: varchar(20) not null ('info' | 'warn' | 'critical')
  - tags: jsonb (タグ配列)
  - publish_from: timestamptz not null (公開開始日時)
  - publish_to: timestamptz (公開終了日時、NULL=無期限)
  - audience: varchar(50) not null ('all' | 'internal' | 'site:narita' | 'site:shinkiba')
  - attachments: jsonb (添付ファイル配列)
  - notification_plan: jsonb (通知設定)
  - 監査列: created_at, updated_at
  - 論理削除: deleted_at, deleted_by

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251224_001'
down_revision = '20251216_004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """app.announcements テーブルを作成"""
    
    # app スキーマが存在しない場合は作成
    op.execute("CREATE SCHEMA IF NOT EXISTS app;")
    
    # announcements テーブル作成
    op.execute("""
        CREATE TABLE app.announcements (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            body_md TEXT NOT NULL,
            severity VARCHAR(20) NOT NULL DEFAULT 'info',
            tags JSONB DEFAULT '[]'::jsonb,
            publish_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            publish_to TIMESTAMP WITH TIME ZONE DEFAULT NULL,
            audience VARCHAR(50) NOT NULL DEFAULT 'all',
            attachments JSONB DEFAULT '[]'::jsonb,
            notification_plan JSONB DEFAULT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
            deleted_by TEXT DEFAULT NULL,
            CONSTRAINT chk_severity CHECK (severity IN ('info', 'warn', 'critical')),
            CONSTRAINT chk_audience CHECK (audience IN ('all', 'internal', 'site:narita', 'site:shinkiba'))
        );
    """)
    
    # インデックス追加
    op.execute("""
        CREATE INDEX idx_announcements_publish_from 
        ON app.announcements (publish_from DESC);
    """)
    
    op.execute("""
        CREATE INDEX idx_announcements_deleted_at 
        ON app.announcements (deleted_at) 
        WHERE deleted_at IS NULL;
    """)
    
    op.execute("""
        CREATE INDEX idx_announcements_audience 
        ON app.announcements (audience);
    """)
    
    # コメント追加
    op.execute("""
        COMMENT ON TABLE app.announcements IS 
        'システムのお知らせ（アナウンスメント）。公開期間・対象・重要度を持つ';
    """)
    op.execute("COMMENT ON COLUMN app.announcements.id IS 'お知らせID（PK）';")
    op.execute("COMMENT ON COLUMN app.announcements.title IS 'タイトル';")
    op.execute("COMMENT ON COLUMN app.announcements.body_md IS '本文（Markdown形式）';")
    op.execute("COMMENT ON COLUMN app.announcements.severity IS '重要度（info/warn/critical）';")
    op.execute("COMMENT ON COLUMN app.announcements.tags IS 'タグ配列（JSONB）';")
    op.execute("COMMENT ON COLUMN app.announcements.publish_from IS '公開開始日時';")
    op.execute("COMMENT ON COLUMN app.announcements.publish_to IS '公開終了日時（NULL=無期限）';")
    op.execute("COMMENT ON COLUMN app.announcements.audience IS '対象（all/internal/site:narita/site:shinkiba）';")
    op.execute("COMMENT ON COLUMN app.announcements.attachments IS '添付ファイル配列（JSONB）';")
    op.execute("COMMENT ON COLUMN app.announcements.notification_plan IS '通知設定（JSONB）';")


def downgrade() -> None:
    """app.announcements テーブルを削除"""
    op.execute("DROP TABLE IF EXISTS app.announcements CASCADE;")
