"""add_notification_outbox_failure_type

Revision ID: 20251225_001
Revises: 20251224_006
Create Date: 2025-12-25

notification_outbox テーブルに failure_type カラムを追加

目的：
  LINE通知基盤の拡張（TEMPORARY/PERMANENT失敗分類）
  - TEMPORARY: 一時的な失敗（タイムアウト、ネットワークエラー等）→ リトライ対象
  - PERMANENT: 恒久的な失敗（バリデーションエラー、認証失敗等）→ リトライなし

変更内容：
  - failure_type VARCHAR(20) カラムを追加
  - デフォルト値: 'TEMPORARY'（既存の failed レコードはリトライ可能と見なす）
  - NULL許可（pending/sent/skipped 時は NULL）

理由：
  失敗の種類によってリトライ戦略を変える必要があるため：
  - TEMPORARY: 指数バックオフでリトライ（1→5→30→60分）
  - PERMANENT: 即座に failed に遷移し、リトライしない
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251225_001'
down_revision = '20251224_006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """failure_type カラムを追加"""
    
    op.execute("""
        ALTER TABLE app.notification_outbox 
        ADD COLUMN failure_type VARCHAR(20) DEFAULT NULL;
    """)
    
    # 既存の failed レコードに TEMPORARY を設定（互換性のため）
    op.execute("""
        UPDATE app.notification_outbox 
        SET failure_type = 'TEMPORARY' 
        WHERE status = 'failed' AND failure_type IS NULL;
    """)
    
    # コメント追加
    op.execute("""
        COMMENT ON COLUMN app.notification_outbox.failure_type IS 
        '失敗タイプ（TEMPORARY: リトライ可能、PERMANENT: リトライ不可、NULL: 未失敗）';
    """)


def downgrade() -> None:
    """failure_type カラムを削除"""
    
    op.execute("""
        ALTER TABLE app.notification_outbox 
        DROP COLUMN IF EXISTS failure_type;
    """)
