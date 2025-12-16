"""create_forecast_schema_and_jobs_table

Revision ID: 20251216_005
Revises: 20251216_004
Create Date: 2025-12-16 15:00:00.000000

予測ジョブキュー基盤の構築

目的：
  日次/週次/月次予測を非同期実行するためのジョブキューテーブルを作成

スキーマ：forecast
  - 予測関連のテーブル/ビューを集約

テーブル：forecast.forecast_jobs
  - ジョブタイプ（daily_tplus1, weekly, monthly等）別にジョブを管理
  - 重複防止：(job_type, target_date) が queued/running の間はユニーク
  - リトライ機構：attempt/max_attempt による再試行制御
  - ロック機構：locked_at/locked_by によるクレーム制御

カラム仕様：
  - id: uuid PK (自動生成)
  - job_type: text not null ('daily_tplus1', 'daily_tplus7', 'weekly', 'monthly_gamma', 'monthly_landing_14d', 'monthly_landing_21d')
  - target_date: date not null (予測対象日)
  - status: text not null ('queued', 'running', 'succeeded', 'failed')
  - run_after: timestamptz not null (実行可能時刻)
  - locked_at: timestamptz null (ワーカーがクレームした時刻)
  - locked_by: text null (ワーカーID/ホスト名)
  - attempt: int not null default 0 (試行回数)
  - max_attempt: int not null default 3 (最大試行回数)
  - input_snapshot: jsonb not null default '{}' (入力パラメータスナップショット)
  - last_error: text null (最後のエラーメッセージ)
  - created_at: timestamptz not null default now()
  - updated_at: timestamptz not null default now()
  - started_at: timestamptz null (実行開始時刻)
  - finished_at: timestamptz null (実行終了時刻)

制約：
  - UNIQUE (job_type, target_date) WHERE status IN ('queued', 'running')
    → 同一ジョブの重複投入を防止（ただし queued/running の間のみ）

インデックス：
  - status, run_after でポーリングクエリを高速化
  - job_type, target_date で検索を高速化

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '20251216_005'
down_revision = '20251216_004'  # 20251216_004_add_soft_delete_to_reserve_daily_manual
branch_labels = None
depends_on = None


def upgrade() -> None:
    """forecast スキーマと forecast_jobs テーブルを作成"""
    
    # 1. forecast スキーマを作成
    op.execute("CREATE SCHEMA IF NOT EXISTS forecast;")
    
    # 2. forecast.forecast_jobs テーブルを作成
    op.execute("""
        CREATE TABLE forecast.forecast_jobs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            job_type text NOT NULL,
            target_date date NOT NULL,
            status text NOT NULL,
            run_after timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            locked_at timestamp with time zone,
            locked_by text,
            attempt integer NOT NULL DEFAULT 0,
            max_attempt integer NOT NULL DEFAULT 3,
            input_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
            last_error text,
            created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            started_at timestamp with time zone,
            finished_at timestamp with time zone,
            
            CONSTRAINT chk_forecast_jobs_status CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
            CONSTRAINT chk_forecast_jobs_job_type CHECK (
                job_type IN (
                    'daily_tplus1', 
                    'daily_tplus7', 
                    'weekly', 
                    'monthly_gamma', 
                    'monthly_landing_14d', 
                    'monthly_landing_21d'
                )
            ),
            CONSTRAINT chk_forecast_jobs_attempt CHECK (attempt >= 0),
            CONSTRAINT chk_forecast_jobs_max_attempt CHECK (max_attempt >= 1),
            CONSTRAINT chk_forecast_jobs_attempt_le_max CHECK (attempt <= max_attempt)
        );
    """)
    
    # 3. 部分ユニークインデックス（重複防止）
    # queued/running の間だけ (job_type, target_date) がユニーク
    op.execute("""
        CREATE UNIQUE INDEX idx_forecast_jobs_unique_active
        ON forecast.forecast_jobs (job_type, target_date)
        WHERE status IN ('queued', 'running');
    """)
    
    # 4. ポーリング用インデックス（status, run_after）
    op.execute("""
        CREATE INDEX idx_forecast_jobs_polling
        ON forecast.forecast_jobs (status, run_after)
        WHERE status = 'queued';
    """)
    
    # 5. 検索用インデックス（job_type, target_date, status）
    op.execute("""
        CREATE INDEX idx_forecast_jobs_search
        ON forecast.forecast_jobs (job_type, target_date, status);
    """)
    
    # 6. テーブルコメント（ドキュメンテーション）
    op.execute("""
        COMMENT ON TABLE forecast.forecast_jobs IS 
        '予測ジョブキュー: 日次/週次/月次予測の非同期実行を管理';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.id IS 
        'ジョブID（UUID、自動生成）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.job_type IS 
        'ジョブタイプ（daily_tplus1, weekly, monthly_gamma等）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.target_date IS 
        '予測対象日（日次なら予測日、月次なら対象月初日）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.status IS 
        'ジョブステータス（queued/running/succeeded/failed）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.run_after IS 
        '実行可能時刻（この時刻以降にワーカーがピックアップ可能）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.locked_at IS 
        'ワーカーがクレームした時刻（排他制御用）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.locked_by IS 
        'ワーカーID/ホスト名（排他制御用）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.attempt IS 
        '試行回数（0始まり、失敗時にインクリメント）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.max_attempt IS 
        '最大試行回数（この回数を超えたら諦める）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.input_snapshot IS 
        '入力パラメータのスナップショット（JSON）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN forecast.forecast_jobs.last_error IS 
        '最後のエラーメッセージ（失敗時にセット）';
    """)
    
    # 7. app_user, app_readonly への権限付与（ロールが存在する場合のみ）
    # DO ブロックでロール存在チェックを行い、存在する場合のみGRANT実行
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                GRANT USAGE ON SCHEMA forecast TO app_user;
                GRANT SELECT, INSERT, UPDATE, DELETE ON forecast.forecast_jobs TO app_user;
            END IF;
            
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly') THEN
                GRANT USAGE ON SCHEMA forecast TO app_readonly;
                GRANT SELECT ON forecast.forecast_jobs TO app_readonly;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """forecast.forecast_jobs テーブルと forecast スキーマを削除"""
    
    # 1. インデックスを削除（テーブル削除で自動削除されるが明示的に記載）
    op.execute("DROP INDEX IF EXISTS forecast.idx_forecast_jobs_search;")
    op.execute("DROP INDEX IF EXISTS forecast.idx_forecast_jobs_polling;")
    op.execute("DROP INDEX IF EXISTS forecast.idx_forecast_jobs_unique_active;")
    
    # 2. テーブルを削除
    op.execute("DROP TABLE IF EXISTS forecast.forecast_jobs;")
    
    # 3. スキーマを削除（他にテーブルがあれば失敗する）
    op.execute("DROP SCHEMA IF EXISTS forecast CASCADE;")
