"""mart: repoint MV/VIEW definitions to v_receive_* (no wrapper dependency)

Revision ID: 20251105_115452784
Revises: 20251105_101233931
Create Date: 2025-11-05 02:54:53.576123

"""

from pathlib import Path

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251105_115452784"
down_revision = "20251105_101233931"
branch_labels = None
depends_on = None

# SQL定義ファイルのパス（マテビュー・ビュー定義）
SQL_DIR = Path(__file__).resolve().parents[2] / "alembic" / "sql" / "mart"

# 適用するSQLファイル（既に v_receive_* を参照している定義を再適用）
SQL_FILES = [
    "v_receive_daily.sql",
    "v_receive_weekly.sql",
    "v_receive_monthly.sql",
    "v_target_card_per_day.sql",
    "mv_inb5y_week_profile_min.sql",
    "mv_inb_avg5y_day_biz.sql",
    "mv_inb_avg5y_day_scope.sql",
    "mv_inb_avg5y_weeksum_biz.sql",
]

# マテビュー一覧（DROP IF EXISTS してから再作成が必要）
MATERIALIZED_VIEWS = [
    "mart.mv_inb5y_week_profile_min",
    "mart.mv_inb_avg5y_day_biz",
    "mart.mv_inb_avg5y_day_scope",
    "mart.mv_inb_avg5y_weeksum_biz",
]


def upgrade() -> None:
    """
    各SQLファイルを実行して、ビュー/マテビューの定義を最新化。
    既に v_receive_* を参照するように修正済みの定義を適用。

    マテビューは CREATE OR REPLACE がサポートされていないため、
    DROP IF EXISTS してから再作成する。
    """
    # マテビューを一旦削除
    for mv in MATERIALIZED_VIEWS:
        op.execute(f"DROP MATERIALIZED VIEW IF EXISTS {mv} CASCADE;")

    # 全SQLファイルを適用
    for sql_file in SQL_FILES:
        sql_path = SQL_DIR / sql_file
        if not sql_path.exists():
            op.execute(f"-- NOTICE: {sql_file} not found at {sql_path}")
            continue

        sql_text = sql_path.read_text(encoding="utf-8")
        op.execute(f"-- Applying: {sql_file}")
        op.execute(sql_text)
        op.execute(f"-- Applied: {sql_file}")


def downgrade() -> None:
    """
    非破壊ポリシーに沿って何もしない。
    ビュー/マテビューの定義は後方互換性を保持しているため、
    downgrade による削除は行わない。
    """
    pass
