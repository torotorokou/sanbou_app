"""add_semantic_interval_columns_to_forecast_results

Revision ID: 20251218_002
Revises: 20251218_001
Create Date: 2025-12-18 17:00:00.000000

予測区間カラムの意味論的命名追加

目的：
  p10/p50/p90 が統計的に誤解を招く命名のため、正確な命名のカラムを追加
  
問題：
  - p50: Quantile回帰による50%分位点（正しい命名）
  - p90: Quantile回帰による90%分位点（正しい命名）  
  - p10: p50からσを逆算して計算（p50 - 1.28σ）= 分位点ではない（誤解を招く命名）
  
解決策：
  - 新カラムを追加し、統計的に正確な命名にする
  - 既存カラム（p10/p50/p90）は互換性のため残す（Phase 2以降で段階的廃止）
  
新カラム：
  - median: p50と同じ（50%分位点、Quantile回帰）
  - lower_1sigma: p10と同じ（median - 1.28σ、正規分布仮定）
  - upper_quantile_90: p90と同じ（90%分位点、Quantile回帰）

移行戦略：
  - Phase 1（このマイグレーション）: 新カラム追加、既存データ移行
  - Phase 2（2週間後）: 読み出し側を新カラム優先に変更
  - Phase 3（4-6週間後）: 旧カラム（p10/p50/p90）削除

参考：
  - 調査レポート: docs/development/forecast_interval_semantics_investigation.md
  - 移行計画: docs/development/forecast_interval_migration_plan.md
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251218_002'
down_revision = '20251218_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================
    # 1. 新カラム追加
    # ==========================================
    op.add_column(
        'daily_forecast_results',
        sa.Column('median', sa.Numeric(precision=18, scale=3), nullable=True),
        schema='forecast'
    )
    
    op.add_column(
        'daily_forecast_results',
        sa.Column('lower_1sigma', sa.Numeric(precision=18, scale=3), nullable=True),
        schema='forecast'
    )
    
    op.add_column(
        'daily_forecast_results',
        sa.Column('upper_quantile_90', sa.Numeric(precision=18, scale=3), nullable=True),
        schema='forecast'
    )
    
    # ==========================================
    # 2. コメント追加（統計的意味を明示）
    # ==========================================
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.median IS 
        '中央値（50%分位点）: Quantile回帰（alpha=0.5）による予測値。p50と同じ値だが意味が明確。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.lower_1sigma IS 
        '下限（median - 1.28σ）: 正規分布を仮定し、p90とp50の差からσを逆算して計算。真の10%分位点ではない。p10と同じ値。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.upper_quantile_90 IS 
        '上限（90%分位点）: Quantile回帰（alpha=0.9）による予測値。p90と同じ値。';
    """)
    
    # 既存カラムにもコメント追加（誤解防止）
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.p50 IS 
        '中央値（50%分位点、旧命名）: medianを使用してください。互換性のため残存。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.p10 IS 
        '下限（旧命名、誤解を招く）: lower_1sigmaを使用してください。実際は分位点ではなくσ由来（p50 - 1.28σ）。互換性のため残存。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.p90 IS 
        '上限（90%分位点、旧命名）: upper_quantile_90を使用してください。互換性のため残存。';
    """)
    
    # ==========================================
    # 3. 既存データの移行
    # ==========================================
    op.execute("""
        UPDATE forecast.daily_forecast_results
        SET 
            median = p50,
            lower_1sigma = p10,
            upper_quantile_90 = p90
        WHERE median IS NULL;
    """)
    
    print("✅ Phase 1 完了: 新カラム追加・既存データ移行完了")
    print("📋 次のステップ:")
    print("   - Phase 2: コードを新カラム優先に変更（2週間後）")
    print("   - Phase 3: 旧カラム削除（4-6週間後、全クライアント移行後）")


def downgrade() -> None:
    """
    ロールバック処理
    新カラムを削除（旧カラムは無傷）
    """
    # コメント削除
    op.execute("COMMENT ON COLUMN forecast.daily_forecast_results.p50 IS NULL;")
    op.execute("COMMENT ON COLUMN forecast.daily_forecast_results.p10 IS NULL;")
    op.execute("COMMENT ON COLUMN forecast.daily_forecast_results.p90 IS NULL;")
    
    # 新カラム削除
    op.drop_column('daily_forecast_results', 'upper_quantile_90', schema='forecast')
    op.drop_column('daily_forecast_results', 'lower_1sigma', schema='forecast')
    op.drop_column('daily_forecast_results', 'median', schema='forecast')
    
    print("⏪ ロールバック完了: 新カラム削除（旧カラムは無傷）")
