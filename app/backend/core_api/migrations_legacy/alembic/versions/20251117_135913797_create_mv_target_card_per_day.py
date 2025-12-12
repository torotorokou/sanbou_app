"""
create mv_target_card_per_day with indexes

Purpose:
  既存の VIEW mart.v_target_card_per_day をマテリアライズドビュー化して高速化する。
  
Design:
  - VIEW定義のSELECT文をそのまま再利用（重複を避ける）
  - UNIQUE INDEX on ddate を付与（REFRESH CONCURRENTLY 要件 + 単一日検索最適化）
  - (iso_year, iso_week) の複合INDEX（週次集計クエリ最適化）
  - date_trunc('month', ddate) の関数INDEX（月次範囲検索最適化）
  
Usage:
  - DashboardTargetRepository の get_by_date_optimized() で参照
  - /core_api/dashboard/target エンドポイントがこのMVを使用
  
Refresh Strategy:
  - 日次で REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;
  - ETL完了後の自動実行を推奨（plan_worker or 別途バッチタスク）
  - 手動実行も可能（Makefile に refresh タスクを追加予定）

Rollback Safety:
  - 既存の VIEW mart.v_target_card_per_day は削除しない
  - MVが問題あればRepositoryを元のVIEW参照に戻すだけで済む
  - downgrade() で MV と INDEX を DROP する

Revision ID: 20251117_135913797
Revises: 20251113_170000000
"""

from alembic import op, context
import sqlalchemy as sa
from pathlib import Path

# .sql 正本の配置ディレクトリ
BASE = Path("/backend/migrations/alembic/sql/mart")

# Alembic identifiers
revision = "20251117_135913797"
down_revision = "20251114_090304320"  # 現在のDBリビジョン(mergepoint)
branch_labels = None
depends_on = None


def _exists(qualified: str) -> bool:
    """
    qualified: 'mart.mv_xxx' のようなスキーマ付オブジェクト名。
    オフライン(--sql)は常に False を返し、CREATE句を必ず出す（新規ブート用）。
    オンライン時のみ to_regclass で実在判定。
    """
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    return bool(
        conn.execute(sa.text("SELECT to_regclass(:q) IS NOT NULL"), {"q": qualified}).scalar()
    )


def _read_sql(name_wo_ext: str) -> str:
    """SQL正本ファイル読み込み"""
    p = BASE / f"{name_wo_ext}.sql"
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def _ensure_mv(name: str, create_sql_name: str, indexes: list[str]) -> None:
    """
    MVの作成または既存MVのREFRESH
    
    Args:
        name: 'mart.mv_xxx' 形式のMV名
        create_sql_name: BASE直下の .sql ファイル名（拡張子なし）
        indexes: 付与すべきINDEX文のリスト（'CREATE UNIQUE INDEX IF NOT EXISTS ...' 形式）
    """
    if not _exists(name):
        # 新規（またはオフライン生成）: CREATE + INDEX
        op.execute(_read_sql(create_sql_name))
        for idx in indexes:
            op.execute(idx)
    else:
        # 既存: 一意インデックスを担保してから CONCURRENTLY でREFRESH
        for idx in indexes:
            op.execute(idx)
        op.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {name};")


def upgrade() -> None:
    """
    マテリアライズドビュー mart.mv_target_card_per_day の作成と関連インデックスの設定
    
    インデックス設計の根拠:
    1. UNIQUE INDEX on ddate
       - 目的: REFRESH CONCURRENTLY の要件を満たす + 単一日検索の最適化
       - 対象クエリ: WHERE ddate = :target_date (Repository.get_by_date_optimized)
       - 月次範囲検索 (WHERE ddate BETWEEN...) もこのインデックスでカバー
    
    2. INDEX on (iso_year, iso_week)
       - 目的: 週次集計の高速化
       - 対象クエリ: WHERE iso_year = X AND iso_week = Y (週次目標/実績の集計)
    
    注意:
    - date_trunc('month', ddate) の関数INDEXは作成しない
      → date_trunc関数はSTABLE（not IMMUTABLE）のため、MV上では使用不可
      → 月次範囲検索は ddate の UNIQUE INDEX (B-tree) で十分カバーされる
    """
    _ensure_mv(
        "mart.mv_target_card_per_day",
        "mv_target_card_per_day",
        [
            # 1. UNIQUE INDEX (REFRESH CONCURRENTLY 要件 + 単一日検索最適化)
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_target_card_per_day_ddate "
            "ON mart.mv_target_card_per_day (ddate);",
            
            # 2. 週次集計用の複合INDEX
            "CREATE INDEX IF NOT EXISTS ix_mv_target_card_per_day_iso_week "
            "ON mart.mv_target_card_per_day (iso_year, iso_week);",
        ],
    )


def downgrade() -> None:
    """
    マテリアライズドビューとインデックスの削除
    
    注意:
    - VIEW mart.v_target_card_per_day は削除しない（既存機能への影響を最小化）
    - Repository を元の VIEW 参照に戻せば、完全にロールバック可能
    """
    # インデックス削除（MVと一緒に削除されるが、明示的に記述）
    op.execute("DROP INDEX IF EXISTS mart.ix_mv_target_card_per_day_iso_week;")
    op.execute("DROP INDEX IF EXISTS mart.ux_mv_target_card_per_day_ddate;")
    
    # マテリアライズドビュー削除
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_target_card_per_day;")
