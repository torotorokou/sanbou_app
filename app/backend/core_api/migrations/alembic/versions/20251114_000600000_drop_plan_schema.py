"""Drop plan schema (unused)

Revision ID: 20251114_000600000
Revises: 20251113_180000000
Create Date: 2025-11-14 00:06:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251114_000600000'
down_revision: Union[str, None] = '20251113_180000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    plan スキーマを削除
    
    理由:
    - コードベース全体で plan スキーマへの参照が見つからない
    - plan.monthly_target テーブルは空（0行）
    - 現在使用されていない未使用スキーマと判断
    
    影響範囲:
    - plan スキーマとその中の全オブジェクト（plan.monthly_target テーブル）を削除
    """
    
    # plan スキーマが存在する場合のみ削除
    op.execute("""
        DROP SCHEMA IF EXISTS plan CASCADE;
    """)


def downgrade() -> None:
    """
    ロールバック: plan スキーマとmonthly_targetテーブルを再作成
    
    注意: データは復元されません（元々0行だったため問題なし）
    """
    
    # plan スキーマを再作成
    op.execute("""
        CREATE SCHEMA IF NOT EXISTS plan;
    """)
    
    # monthly_target テーブルを再作成
    op.execute("""
        CREATE TABLE IF NOT EXISTS plan.monthly_target (
            month_date DATE NOT NULL,
            segment TEXT NOT NULL,
            metric TEXT NOT NULL,
            scenario TEXT,
            value NUMERIC,
            unit TEXT,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (month_date, segment, metric, scenario)
        );
    """)
    
    # インデックスを再作成（もし必要であれば）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_plan_monthly_target_date 
        ON plan.monthly_target(month_date);
    """)
