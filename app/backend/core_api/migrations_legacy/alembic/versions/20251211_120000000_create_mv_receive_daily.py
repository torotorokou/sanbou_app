"""create mv_receive_daily materialized view

Purpose:
  mart.v_receive_daily (VIEW) を mart.mv_receive_daily (MATERIALIZED VIEW) として複製。
  毎回 stg テーブルの集計を実行するコストを削減し、/inbound/daily API を高速化する。

Design:
  - 既存の v_receive_daily の定義をそのまま MV として実装
  - UNIQUE INDEX on ddate (REFRESH CONCURRENTLY 要件 + 単一日検索最適化)
  - INDEX on (iso_year, iso_week) (週次集計最適化)
  - 既存の VIEW は削除しない（ロールバック時に使用）

Refresh Strategy:
  - CSV アップロード完了後に REFRESH MATERIALIZED VIEW CONCURRENTLY
  - make refresh-mv-receive-daily タスクを追加予定

Performance Impact:
  - /inbound/daily API のレスポンスタイム 50-70% 短縮を期待
  - 特に前月/前年比較を含むクエリで効果大

Rollback:
  - downgrade() で MV を DROP
  - Repository を元の VIEW 参照に戻せば完全にロールバック可能

Revision ID: 20251211_120000000
Revises: 20251211_110000000
Create Date: 2025-12-11 12:00:00
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251211_120000000"
down_revision = "20251211_110000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    mart.mv_receive_daily マテリアライズドビューの作成

    設計:
    1. 既存の mart.v_receive_daily の定義を基に MV を作成
    2. UNIQUE INDEX on ddate (REFRESH CONCURRENTLY 要件)
    3. INDEX on (iso_year, iso_week) (週次集計用)
    """
    print("📌 Creating mart.mv_receive_daily materialized view...")

    # 1. Materialized View の作成
    # 注意: ここでは既存の VIEW 定義をそのまま使用
    # 実際の VIEW 定義は mart.v_receive_daily から取得
    op.execute(
        """
        CREATE MATERIALIZED VIEW mart.mv_receive_daily AS
        SELECT * FROM mart.v_receive_daily;
    """
    )
    print("  ✓ Created mart.mv_receive_daily")

    # 2. UNIQUE INDEX (REFRESH CONCURRENTLY 要件 + 単一日検索最適化)
    op.execute(
        """
        CREATE UNIQUE INDEX ux_mv_receive_daily_ddate
        ON mart.mv_receive_daily (ddate);
    """
    )
    print("  ✓ Created ux_mv_receive_daily_ddate (UNIQUE)")

    # 3. 週次集計用の複合INDEX
    op.execute(
        """
        CREATE INDEX ix_mv_receive_daily_iso_week
        ON mart.mv_receive_daily (iso_year, iso_week);
    """
    )
    print("  ✓ Created ix_mv_receive_daily_iso_week")

    print("✅ mart.mv_receive_daily created successfully")
    print(
        "⚠️  Next step: Run 'REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_receive_daily;'"
    )
    print("⚠️  Repository を mv_receive_daily 参照に変更してください")


def downgrade() -> None:
    """
    マテリアライズドビューとインデックスの削除

    注意:
    - VIEW mart.v_receive_daily は削除しない（既存機能への影響を最小化）
    - Repository を元の VIEW 参照に戻せば、完全にロールバック可能
    """
    print("📌 Dropping mart.mv_receive_daily materialized view...")

    # インデックス削除（MVと一緒に削除されるが、明示的に記述）
    op.execute("DROP INDEX IF EXISTS mart.ix_mv_receive_daily_iso_week;")
    print("  ✓ Dropped ix_mv_receive_daily_iso_week")

    op.execute("DROP INDEX IF EXISTS mart.ux_mv_receive_daily_ddate;")
    print("  ✓ Dropped ux_mv_receive_daily_ddate")

    # マテリアライズドビュー削除
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_receive_daily;")
    print("  ✓ Dropped mart.mv_receive_daily")

    print("✅ mart.mv_receive_daily dropped successfully")
