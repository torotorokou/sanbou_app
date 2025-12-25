"""
manage materialized views: mart.*

安全版:
- 既存DB: REFRESH MATERIALIZED VIEW CONCURRENTLY のみ（事前に一意INDEXをIF NOT EXISTSで張る）
- 新規DB/オフライン(--sql): CREATE MATERIALIZED VIEW + INDEX を出力

Revision ID: 20251104_162109457
Revises: 20251104_160703155
"""

from pathlib import Path

import sqlalchemy as sa
from alembic import context, op

# .sql 正本の配置ディレクトリ（MV本体）
BASE = Path("/backend/migrations/alembic/sql/mart")

# Alembic identifiers
revision = "20251104_162109457"
down_revision = "20251104_160703155"
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
    p = BASE / f"{name_wo_ext}.sql"
    with open(p, encoding="utf-8") as f:
        return f.read()


def _ensure_mv(name: str, create_sql_name: str, indexes: list[str]) -> None:
    """
    name: 'mart.mv_xxx'
    create_sql_name: BASE直下の .sql（拡張子なし）
    indexes: 付与すべきINDEX文（'CREATE UNIQUE INDEX IF NOT EXISTS ...'）
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
    # 依存する通常VIEW（mart.receive_daily 等）が事前リビジョンで定義済みである前提

    _ensure_mv(
        "mart.mv_inb5y_week_profile_min",
        "mv_inb5y_week_profile_min",
        [
            # REFRESH CONCURRENTLY要件: ユニークインデックス
            "CREATE UNIQUE INDEX IF NOT EXISTS mv_inb5y_week_profile_min_pk "
            "ON mart.mv_inb5y_week_profile_min (iso_week);",
        ],
    )

    _ensure_mv(
        "mart.mv_inb_avg5y_day_biz",
        "mv_inb_avg5y_day_biz",
        [
            "CREATE UNIQUE INDEX IF NOT EXISTS mv_inb_avg5y_day_biz_pk "
            "ON mart.mv_inb_avg5y_day_biz (iso_week, iso_dow);",
        ],
    )

    _ensure_mv(
        "mart.mv_inb_avg5y_weeksum_biz",
        "mv_inb_avg5y_weeksum_biz",
        [
            "CREATE UNIQUE INDEX IF NOT EXISTS mv_inb_avg5y_weeksum_biz_pk "
            "ON mart.mv_inb_avg5y_weeksum_biz (iso_week);",
        ],
    )

    _ensure_mv(
        "mart.mv_inb_avg5y_day_scope",
        "mv_inb_avg5y_day_scope",
        [
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_inb_avg5y_day_scope "
            "ON mart.mv_inb_avg5y_day_scope (scope, iso_week, iso_dow);",
        ],
    )


def downgrade() -> None:
    # 運用ポリシー次第：ここはNO-OPでも良いが、従来通りDROPにしておく
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_day_scope;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_weeksum_biz;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_day_biz;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb5y_week_profile_min;")
