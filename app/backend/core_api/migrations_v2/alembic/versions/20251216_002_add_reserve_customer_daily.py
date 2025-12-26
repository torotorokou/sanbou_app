"""add_reserve_customer_daily

Revision ID: 6807c2215b75
Revises: 1d57288e056c
Create Date: 2025-12-16 11:21:07.722547

Phase 2: stg.reserve_customer_daily テーブル追加

目的：
  顧客ごとの予約一覧を管理（日付×顧客）

テーブル仕様：
  - PK: id (bigserial)
  - reserve_date: date not null
  - customer_cd: text not null
  - customer_name: text (スナップショット用途)
  - planned_trucks: integer not null default 0
  - is_fixed_customer: boolean not null default false
  - 監査列: created_at, updated_at (timestamptz)
  - 任意: note, created_by, updated_by
  - UNIQUE制約: (reserve_date, customer_cd)
  - INDEX: (reserve_date), (reserve_date, is_fixed_customer)
  - 制約: planned_trucks >= 0

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "6807c2215b75"
down_revision = "1d57288e056c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """stg.reserve_customer_daily テーブルを作成"""
    op.execute(
        """
        CREATE TABLE stg.reserve_customer_daily (
            id bigserial PRIMARY KEY,
            reserve_date date NOT NULL,
            customer_cd text NOT NULL,
            customer_name text,
            planned_trucks integer NOT NULL DEFAULT 0,
            is_fixed_customer boolean NOT NULL DEFAULT false,
            note text,
            created_by text,
            updated_by text,
            created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT chk_planned_trucks_non_negative CHECK (planned_trucks >= 0),
            CONSTRAINT uq_reserve_customer_daily_date_customer UNIQUE (reserve_date, customer_cd)
        );
    """
    )

    # インデックス作成
    op.execute(
        """
        CREATE INDEX idx_reserve_customer_daily_date
        ON stg.reserve_customer_daily (reserve_date);
    """
    )
    op.execute(
        """
        CREATE INDEX idx_reserve_customer_daily_date_fixed
        ON stg.reserve_customer_daily (reserve_date, is_fixed_customer);
    """
    )

    # コメント追加（ドキュメンテーション）
    op.execute(
        """
        COMMENT ON TABLE stg.reserve_customer_daily IS
        '顧客ごとの予約一覧。manual入力がない日付はこのテーブルから集計';
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN stg.reserve_customer_daily.reserve_date IS '予約日';
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN stg.reserve_customer_daily.customer_cd IS '顧客コード';
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN stg.reserve_customer_daily.customer_name IS '顧客名（スナップショット）';
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN stg.reserve_customer_daily.planned_trucks IS '予定台数';
    """
    )
    op.execute(
        """
        COMMENT ON COLUMN stg.reserve_customer_daily.is_fixed_customer IS '固定客フラグ';
    """
    )


def downgrade() -> None:
    """stg.reserve_customer_daily テーブルを削除"""
    op.execute("DROP TABLE IF EXISTS stg.reserve_customer_daily CASCADE;")
