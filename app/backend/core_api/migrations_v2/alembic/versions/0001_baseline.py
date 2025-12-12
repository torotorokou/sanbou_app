"""Baseline revision for Alembic v2

Revision ID: 0001_baseline
Revises: 
Create Date: 2025-12-12 16:00:00.000000

★ このマイグレーションについて:
  - Alembic v2 の起点となるベースラインリビジョンです
  - upgrade() / downgrade() は意図的に空（no-op）です
  - このリビジョンをstampする前に、schema_baseline.sqlを適用することが前提です
  
★ 前提条件:
  1. データベースが空の状態 または 既存データを保持したまま移行する場合
  2. migrations_v2/sql/schema_baseline.sql が適用済みであること
  3. scripts/db/bootstrap_roles.sql が適用済みであること（app_readonlyロール等）
  
★ 使用方法:
  # 新規環境（vm_stg / vm_prod）の場合:
  1. make db-apply-snapshot-v2-env ENV=vm_stg
  2. make db-bootstrap-roles-env ENV=vm_stg
  3. make al-stamp-v2-env ENV=vm_stg REV=0001_baseline
  4. make al-up-v2-env ENV=vm_stg  # 以降の変更を適用
  
  # local_dev から移行する場合:
  1. 既存DBはそのまま（データ保持）
  2. make al-stamp-v2-env ENV=local_dev REV=0001_baseline
  3. 以降は make al-up-v2-env ENV=local_dev で新規変更を適用

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    このマイグレーションはno-opです。
    schema_baseline.sqlが適用済みであることを前提としています。
    
    ベースラインスキーマには以下が含まれます:
    - public.alembic_version テーブル
    - raw スキーマとテーブル群
    - ref スキーマとテーブル群
    - mart スキーマとビュー/MV群
    - stg スキーマとビュー群
    - kpi スキーマとテーブル群
    - インデックス、関数、権限設定など
    """
    pass


def downgrade() -> None:
    """
    ベースラインからのダウングレードはサポートしていません。
    データベース全体を再構築する場合は、以下の手順を実行してください:
    
    1. make down ENV=<env>
    2. docker volume rm <env>_postgres_data
    3. make up ENV=<env>
    4. make db-apply-snapshot-v2-env ENV=<env>
    5. make db-bootstrap-roles-env ENV=<env>
    6. make al-stamp-v2-env ENV=<env> REV=0001_baseline
    """
    pass
