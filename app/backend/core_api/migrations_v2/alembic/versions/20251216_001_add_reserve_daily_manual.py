"""add_reserve_daily_manual

Revision ID: 1d57288e056c
Revises: 20251212_100000000
Create Date: 2025-12-16 11:18:16.996509

Phase 1: stg.reserve_daily_manual テーブル追加

目的：
  ユーザー手入力の日次予約合計（予約日ごとの合計台数と固定客台数）を管理

テーブル仕様：
  - PK: reserve_date (date)
  - total_trucks: int not null default 0 (合計台数)
  - fixed_trucks: int not null default 0 (固定客台数)
  - 監査列: created_at, updated_at (timestamptz)
  - 任意: note, created_by, updated_by
  - 制約: total_trucks >= 0, fixed_trucks >= 0, fixed_trucks <= total_trucks

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d57288e056c'
down_revision = '20251212_100000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """stg.reserve_daily_manual テーブルを作成"""
    op.execute("""
        CREATE TABLE stg.reserve_daily_manual (
            reserve_date date PRIMARY KEY,
            total_trucks integer NOT NULL DEFAULT 0,
            fixed_trucks integer NOT NULL DEFAULT 0,
            note text,
            created_by text,
            updated_by text,
            created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT chk_total_trucks_non_negative CHECK (total_trucks >= 0),
            CONSTRAINT chk_fixed_trucks_non_negative CHECK (fixed_trucks >= 0),
            CONSTRAINT chk_fixed_trucks_not_exceed_total CHECK (fixed_trucks <= total_trucks)
        );
    """)
    
    # コメント追加（ドキュメンテーション）
    op.execute("""
        COMMENT ON TABLE stg.reserve_daily_manual IS 
        'ユーザー手入力の日次予約合計。manual入力がある日付はこのテーブルを優先';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.reserve_daily_manual.reserve_date IS '予約日（PK）';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.reserve_daily_manual.total_trucks IS '合計台数';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.reserve_daily_manual.fixed_trucks IS '固定客台数';
    """)


def downgrade() -> None:
    """stg.reserve_daily_manual テーブルを削除"""
    op.execute("DROP TABLE IF EXISTS stg.reserve_daily_manual CASCADE;")
