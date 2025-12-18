"""add_model_metrics_table

Revision ID: 20251218_003
Revises: 20251218_002
Create Date: 2025-12-18 18:00:00.000000

モデル精度指標テーブルの追加

目的：
  学習済みモデルの精度指標（MAE/R2等）をDBに保存し、予測結果と紐付け可能にする
  
背景：
  - 現状、精度指標はJSONファイルに出力されているがDBには保存されていない
  - 予測結果（daily_forecast_results）と精度指標が紐付いていない
  - 監査・品質管理のため、学習品質を記録する必要がある
  
解決策：
  - forecast.model_metrics テーブルを追加
  - job_id で forecast_jobs と紐付け
  - MAE/R2等のコア指標と、メタデータ（ハイパーパラメータ等）を保存
  
参考：
  - 調査レポート: docs/development/model_metrics_investigation.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251218_003'
down_revision = '20251218_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """forecast.model_metrics テーブルを作成"""
    
    # ==========================================
    # 1. model_metrics テーブルを作成
    # ==========================================
    op.execute("""
        CREATE TABLE forecast.model_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NULL,
            model_name TEXT NOT NULL,
            model_version TEXT NULL,
            
            -- 学習期間
            train_window_start DATE NOT NULL,
            train_window_end DATE NOT NULL,
            eval_method TEXT NOT NULL,
            
            -- 精度指標（コア）
            mae NUMERIC(18, 6) NOT NULL,
            r2 NUMERIC(18, 6) NOT NULL,
            n_samples INT NOT NULL,
            
            -- 精度指標（追加）
            rmse NUMERIC(18, 6) NULL,
            mape NUMERIC(18, 6) NULL,
            mae_sum_only NUMERIC(18, 6) NULL,
            r2_sum_only NUMERIC(18, 6) NULL,
            
            -- メタデータ
            unit TEXT NOT NULL DEFAULT 'ton',
            metadata JSONB NOT NULL DEFAULT '{}',
            
            -- 監査列
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_model_metrics_job_id 
                FOREIGN KEY (job_id) 
                REFERENCES forecast.forecast_jobs(id) 
                ON DELETE CASCADE,
            
            CONSTRAINT chk_model_metrics_mae CHECK (mae >= 0),
            CONSTRAINT chk_model_metrics_rmse CHECK (rmse IS NULL OR rmse >= 0),
            CONSTRAINT chk_model_metrics_mape CHECK (mape IS NULL OR mape >= 0),
            CONSTRAINT chk_model_metrics_n_samples CHECK (n_samples >= 1),
            CONSTRAINT chk_model_metrics_unit CHECK (unit IN ('ton', 'kg'))
        );
    """)
    
    # ==========================================
    # 2. インデックス作成
    # ==========================================
    op.execute("""
        CREATE INDEX idx_model_metrics_job_id 
        ON forecast.model_metrics(job_id);
    """)
    
    op.execute("""
        CREATE INDEX idx_model_metrics_model_name_version 
        ON forecast.model_metrics(model_name, model_version, train_window_end DESC);
    """)
    
    op.execute("""
        CREATE INDEX idx_model_metrics_created_at 
        ON forecast.model_metrics(created_at DESC);
    """)
    
    # ==========================================
    # 3. テーブル・カラムコメント
    # ==========================================
    op.execute("""
        COMMENT ON TABLE forecast.model_metrics IS 
        '学習済みモデルの精度指標を記録。Walk-forward評価等の結果をDBに保存し、予測結果と紐付ける。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.id IS 
        '精度指標レコードの一意識別子';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.job_id IS 
        '予測ジョブID（forecast.forecast_jobs.id）。学習と予測が同一ジョブの場合に紐付け。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.model_name IS 
        'モデル名（例：daily_tplus1, monthly_gamma）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.model_version IS 
        'モデルバージョン（例：v20251218, bundle hash）。NULL許可（当面未使用）。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.train_window_start IS 
        '学習データの開始日';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.train_window_end IS 
        '学習データの終了日';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.eval_method IS 
        '評価方法（例：walkforward, holdout, cv）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.mae IS 
        'Mean Absolute Error（平均絶対誤差）。単位は unit カラムに依存。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.r2 IS 
        'R² スコア（決定係数）。-∞～1の範囲。1に近いほど良い。負の値も正常（平均値より悪い予測）。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.n_samples IS 
        '評価サンプル数（日数等）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.rmse IS 
        'Root Mean Squared Error（二乗平均平方根誤差）。オプション。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.mape IS 
        'Mean Absolute Percentage Error（平均絶対パーセント誤差）。%単位。オプション。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.mae_sum_only IS 
        '品目合計のみのMAE。補正前の精度を確認するため。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.r2_sum_only IS 
        '品目合計のみのR²。補正前の精度を確認するため。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.unit IS 
        '精度指標の単位（ton or kg）。MAE/RMSEに影響。';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.model_metrics.metadata IS 
        'メタデータ（ハイパーパラメータ、特徴量数、品目数等）をJSONBで保存。';
    """)
    
    print("✅ Phase 1 完了: forecast.model_metrics テーブル作成完了")
    print("📋 次のステップ:")
    print("   - Port/Adapter実装（ModelMetricsRepository）")
    print("   - UseCase拡張（精度指標の保存処理追加）")


def downgrade() -> None:
    """
    ロールバック処理
    model_metrics テーブルを削除
    """
    op.execute("DROP TABLE IF EXISTS forecast.model_metrics CASCADE;")
    
    print("⏪ ロールバック完了: forecast.model_metrics テーブル削除")
