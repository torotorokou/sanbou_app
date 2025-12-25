"""add_soft_delete_to_reserve_daily_manual

Revision ID: 20251216_004
Revises: 20251216_003_add_v_reserve_daily_for_forecast
Create Date: 2025-12-16 12:00:00.000000

論理削除カラムの追加

目的：
  stg.reserve_daily_manual に論理削除（Soft Delete）機能を追加
  既存データを保持しながら、削除済みフラグで管理

追加カラム：
  - deleted_at: timestamp with time zone (削除日時、NULL=未削除)
  - deleted_by: text (削除者、認証実装後に使用)

変更内容：
  - 物理削除から論理削除へ移行
  - 既存データは維持（deleted_at = NULL）
  - SELECT時は deleted_at IS NULL で除外

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251216_004"
down_revision = "11e8fe1cc1d4"  # 20251216_003_add_v_reserve_daily_for_forecast
branch_labels = None
depends_on = None


def upgrade() -> None:
    """論理削除カラムを追加"""

    # deleted_at カラム追加（デフォルトNULL = 未削除）
    op.execute(
        """
        ALTER TABLE stg.reserve_daily_manual
        ADD COLUMN deleted_at timestamp with time zone DEFAULT NULL;
    """
    )

    # deleted_by カラム追加（削除者記録用）
    op.execute(
        """
        ALTER TABLE stg.reserve_daily_manual
        ADD COLUMN deleted_by text DEFAULT NULL;
    """
    )

    # インデックス追加（deleted_at IS NULL の検索を高速化）
    op.execute(
        """
        CREATE INDEX idx_reserve_daily_manual_not_deleted
        ON stg.reserve_daily_manual (reserve_date)
        WHERE deleted_at IS NULL;
    """
    )

    # カラムコメント追加
    op.execute(
        """
        COMMENT ON COLUMN stg.reserve_daily_manual.deleted_at IS
        '論理削除日時（NULL=未削除、値あり=削除済み）';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.reserve_daily_manual.deleted_by IS
        '削除実行者（将来の認証機能で使用）';
    """
    )

    # ビューを再作成（論理削除を除外）
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_reserve_daily_for_forecast AS
        WITH customer_agg AS (
            -- 顧客別データを日次集計
            SELECT
                reserve_date AS date,
                SUM(planned_trucks) AS reserve_trucks,
                SUM(CASE WHEN is_fixed_customer THEN planned_trucks ELSE 0 END) AS reserve_fixed_trucks,
                'customer_agg' AS source
            FROM stg.reserve_customer_daily
            GROUP BY reserve_date
        ),
        manual_data AS (
            -- manual入力データ（論理削除を除外）
            SELECT
                reserve_date AS date,
                total_trucks AS reserve_trucks,
                fixed_trucks AS reserve_fixed_trucks,
                'manual' AS source
            FROM stg.reserve_daily_manual
            WHERE deleted_at IS NULL  -- 論理削除を除外
        ),
        combined AS (
            -- manual優先でデータを統合
            SELECT
                COALESCE(m.date, c.date) AS date,
                COALESCE(m.reserve_trucks, c.reserve_trucks, 0) AS reserve_trucks,
                COALESCE(m.reserve_fixed_trucks, c.reserve_fixed_trucks, 0) AS reserve_fixed_trucks,
                COALESCE(m.source, c.source) AS source
            FROM manual_data m
            FULL OUTER JOIN customer_agg c ON m.date = c.date
            WHERE COALESCE(m.date, c.date) IS NOT NULL
        )
        SELECT
            date,
            reserve_trucks,
            reserve_fixed_trucks,
            CASE
                WHEN reserve_trucks > 0 THEN
                    ROUND(reserve_fixed_trucks::numeric / reserve_trucks::numeric, 4)
                ELSE 0
            END AS reserve_fixed_ratio,
            source
        FROM combined
        ORDER BY date;
    """
    )


def downgrade() -> None:
    """論理削除カラムを削除"""

    # インデックス削除
    op.execute("DROP INDEX IF EXISTS stg.idx_reserve_daily_manual_not_deleted;")

    # カラム削除
    op.execute("ALTER TABLE stg.reserve_daily_manual DROP COLUMN IF EXISTS deleted_by;")
    op.execute("ALTER TABLE stg.reserve_daily_manual DROP COLUMN IF EXISTS deleted_at;")
