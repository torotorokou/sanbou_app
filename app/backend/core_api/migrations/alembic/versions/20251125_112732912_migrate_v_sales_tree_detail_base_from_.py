"""migrate v_sales_tree_detail_base from sandbox to mart

このマイグレーションは、sandbox.v_sales_tree_detail_base を mart スキーマに正式移行します。

背景:
- 既に 20251125_100000000 で mart.v_sales_tree_detail_base が作成済み
- 今回はアプリケーションコード側を mart スキーマに切り替えるための準備
- sandbox.v_sales_tree_detail_base は互換性のため残す

Revision ID: 20251125_112732912
Revises: 20251125_100000000
Create Date: 2025-11-25 02:27:37.274816

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251125_112732912'
down_revision = '20251125_100000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    アプリケーション側の切り替え準備
    
    実際のビュー作成は 20251125_100000000 で完了済み。
    このマイグレーションは記録用。
    
    次のステップ:
    1. アプリケーションコードを mart.v_sales_tree_detail_base に変更
    2. 動作確認後、別のマイグレーションで sandbox.v_sales_tree_* を削除
    """
    print("[INFO] mart.v_sales_tree_detail_base への切り替え準備完了")
    print("[INFO] アプリケーションコードを mart スキーマに変更してください")
    pass


def downgrade() -> None:
    """
    ダウングレード時の処理
    
    アプリケーションコードを sandbox に戻すことが前提。
    ビュー自体は削除しない。
    """
    print("[INFO] ダウングレード: アプリケーションコードを sandbox に戻してください")
    pass
