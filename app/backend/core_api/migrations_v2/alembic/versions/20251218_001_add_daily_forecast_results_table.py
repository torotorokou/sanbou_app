"""add_daily_forecast_results_table

Revision ID: 20251218_001
Revises: 20251216_005
Create Date: 2025-12-18 10:00:00.000000

日次予測結果テーブルの追加

目的：
  日次t+1予測の結果をDBに保存し、API経由で参照可能にする

テーブル：forecast.daily_forecast_results
  - 日次予測結果を格納
  - (target_date, job_id) で一意
  - p10/p50/p90 の3点予測を保存
  - input_snapshot に入力データの詳細を記録

カラム仕様：
  - id: uuid PK (自動生成)
  - target_date: date not null (予測対象日)
  - job_id: uuid not null (forecast.forecast_jobs.id への参照)
  - p50: numeric(18,3) not null (中央値予測、メイン)
  - p10: numeric(18,3) null (下側予測、10パーセンタイル)
  - p90: numeric(18,3) null (上側予測、90パーセンタイル)
  - unit: text not null default 'ton' (単位)
  - generated_at: timestamptz not null default now() (生成日時)
  - input_snapshot: jsonb not null default '{}' (入力データの詳細)

input_snapshot の内容例：
  {
    "actuals_max_date": "2025-12-17",
    "actuals_count": 365,
    "reserve_exists": true,
    "reserve_trucks": 45,
    "reserve_fixed_ratio": 0.67,
    "model_version": "final_fast_balanced",
    "from_date": "2024-12-18",
    "to_date": "2025-12-17"
  }

制約：
  - UNIQUE (target_date, job_id): 同一ジョブで同じ日付への複数予測を防止
  - job_id は forecast.forecast_jobs.id への FK（CASCADE DELETE）

インデックス：
  - target_date でAPI検索を高速化
  - job_id でジョブ関連検索を高速化

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251218_001'
down_revision = '20251216_005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """forecast.daily_forecast_results テーブルを作成"""
    
    # 1. daily_forecast_results テーブルを作成
    op.execute("""
        CREATE TABLE forecast.daily_forecast_results (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            target_date date NOT NULL,
            job_id uuid NOT NULL,
            p50 numeric(18,3) NOT NULL,
            p10 numeric(18,3),
            p90 numeric(18,3),
            unit text NOT NULL DEFAULT 'ton',
            generated_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            input_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
            
            CONSTRAINT fk_daily_forecast_results_job_id 
                FOREIGN KEY (job_id) 
                REFERENCES forecast.forecast_jobs(id) 
                ON DELETE CASCADE,
            CONSTRAINT uq_daily_forecast_result 
                UNIQUE (target_date, job_id),
            CONSTRAINT chk_daily_forecast_results_unit 
                CHECK (unit IN ('ton', 'kg'))
        );
    """)
    
    # 2. インデックス（target_date での検索）
    op.execute("""
        CREATE INDEX idx_daily_forecast_results_target_date
        ON forecast.daily_forecast_results(target_date);
    """)
    
    # 3. インデックス（job_id での検索）
    op.execute("""
        CREATE INDEX idx_daily_forecast_results_job_id
        ON forecast.daily_forecast_results(job_id);
    """)
    
    # 4. テーブルコメント
    op.execute("""
        COMMENT ON TABLE forecast.daily_forecast_results IS 
        '日次t+1予測結果: 搬入量予測の3点予測（p10/p50/p90）を保存';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.id IS 
        '結果ID（UUID、自動生成）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.target_date IS 
        '予測対象日（明日の日付）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.job_id IS 
        'ジョブID（forecast.forecast_jobs.id への参照）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.p50 IS 
        '中央値予測（メイン予測値）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.p10 IS 
        '下側予測（10パーセンタイル）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.p90 IS 
        '上側予測（90パーセンタイル）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.unit IS 
        '単位（ton or kg）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.generated_at IS 
        '予測生成日時';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.daily_forecast_results.input_snapshot IS 
        '入力データの詳細（実績の期間、予約の有無等）をJSON形式で記録';
    """)
    
    # 5. 環境別アプリケーションユーザーへの権限付与
    # 現在のデータベース名に対応するユーザーのみに権限付与
    # sanbou_dev → sanbou_app_dev のみ
    # sanbou_stg → sanbou_app_stg のみ
    # sanbou_prod → sanbou_app_prod のみ
    op.execute("""
        DO $$
        DECLARE
            current_db text;
            target_user text;
        BEGIN
            -- 現在のデータベース名を取得
            SELECT current_database() INTO current_db;
            
            -- データベース名に応じたユーザー名を決定
            CASE current_db
                WHEN 'sanbou_dev' THEN target_user := 'sanbou_app_dev';
                WHEN 'sanbou_stg' THEN target_user := 'sanbou_app_stg';
                WHEN 'sanbou_prod' THEN target_user := 'sanbou_app_prod';
                ELSE target_user := NULL;
            END CASE;
            
            -- 対応するユーザーが存在する場合のみ権限付与
            IF target_user IS NOT NULL AND EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = target_user) THEN
                EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON forecast.daily_forecast_results TO %I', target_user);
                RAISE NOTICE 'Granted permissions to % for database %', target_user, current_db;
            ELSE
                RAISE NOTICE 'No matching user found for database %', current_db;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    """forecast.daily_forecast_results テーブルを削除"""
    op.execute("DROP TABLE IF EXISTS forecast.daily_forecast_results CASCADE;")
