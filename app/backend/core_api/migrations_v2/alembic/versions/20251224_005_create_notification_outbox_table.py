"""create_notification_outbox_table

Revision ID: 20251224_005
Revises: 20251224_004
Create Date: 2024-12-24

通知Outboxテーブルの作成

目的：
  通知の永続化管理（Transactional Outbox Pattern）
  - 通知要求の登録（enqueue）
  - 送信ステータス管理（pending/sent/failed）
  - リトライ制御（retry_count, next_retry_at）

テーブル仕様：
  - PK: id (UUID)
  - channel: 通知チャネル (email/line/webhook/push)
  - status: ステータス (pending/sent/failed/skipped)
  - recipient_key: 宛先識別子 (email address, user_id等)
  - payload: 通知内容 (title, body, url, meta)
  - 送信管理フィールド (scheduled_at, sent_at, retry_count等)

インデックス：
  - status: pending検索の高速化
  - next_retry_at: リトライ対象の検索
  - created_at: 履歴参照の高速化
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251224_005"
down_revision = "20251224_004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """app.notification_outbox テーブルを作成"""

    op.execute(
        """
        CREATE TABLE app.notification_outbox (
            id UUID PRIMARY KEY,
            channel VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL,
            recipient_key VARCHAR(255) NOT NULL,
            title VARCHAR(500) NOT NULL,
            body TEXT NOT NULL,
            url VARCHAR(1000) DEFAULT NULL,
            meta JSONB DEFAULT NULL,
            scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            sent_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
            retry_count INTEGER NOT NULL DEFAULT 0,
            next_retry_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
            last_error TEXT DEFAULT NULL
        );
    """
    )

    # インデックス作成
    op.execute(
        """
        CREATE INDEX idx_notification_outbox_status
        ON app.notification_outbox(status);
    """
    )

    op.execute(
        """
        CREATE INDEX idx_notification_outbox_next_retry
        ON app.notification_outbox(next_retry_at)
        WHERE next_retry_at IS NOT NULL;
    """
    )

    op.execute(
        """
        CREATE INDEX idx_notification_outbox_created_at
        ON app.notification_outbox(created_at DESC);
    """
    )

    # コメント追加（テーブル仕様の文書化）
    op.execute(
        """
        COMMENT ON TABLE app.notification_outbox IS
        '通知Outbox - Transactional Outbox Patternによる通知管理';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN app.notification_outbox.id IS
        '通知ID（UUID）';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN app.notification_outbox.channel IS
        '通知チャネル（email/line/webhook/push）';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN app.notification_outbox.status IS
        'ステータス（pending/sent/failed/skipped）';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN app.notification_outbox.recipient_key IS
        '宛先識別子（メールアドレス、user_id等）';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN app.notification_outbox.retry_count IS
        'リトライ回数（0始まり）';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN app.notification_outbox.next_retry_at IS
        '次回リトライ時刻（NULL=即座に実行可能）';
    """
    )


def downgrade() -> None:
    """app.notification_outbox テーブルを削除"""

    op.execute("DROP TABLE IF EXISTS app.notification_outbox CASCADE;")
