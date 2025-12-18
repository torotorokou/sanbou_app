"""
Job Executor for Forecast Worker
=================================
Purpose: job_type に応じて適切な予測を実行

Clean Architecture:
- Ports & Adapters パターンに従う
- DB アクセスは Adapters 経由
- ビジネスロジックは UseCase に分離

実行モデル:
1. daily_tplus1: 日次予測 t+1
   - UseCase: RunDailyTplus1ForecastUseCase
   - 入力: DBから実績・予約データ取得
   - 出力: 結果をDBに保存
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend_shared.application.logging import get_module_logger
from .adapters.inbound_actual_repository import PostgreSQLInboundActualRepository
from .adapters.reserve_daily_repository import PostgreSQLReserveDailyRepository
from .adapters.forecast_result_repository import PostgreSQLForecastResultRepository
from .application.run_daily_tplus1_forecast import RunDailyTplus1ForecastUseCase
from .application.run_daily_tplus1_forecast_with_training import RunDailyTplus1ForecastWithTrainingUseCase

logger = get_module_logger(__name__)

# ==========================================
# 定数定義
# ==========================================
# スクリプトベースパス
SCRIPTS_DIR = Path("/backend/scripts")
OUTPUT_DIR = Path("/backend/output")
MODELS_DIR = Path("/backend/models")
DATA_DIR = Path("/backend/data")

# タイムアウト設定（秒）
DEFAULT_TIMEOUT = 1800  # 30分

# ==========================================
# ホワイトリスト定義
# ==========================================
ALLOWED_JOB_TYPES = {
    "daily_tplus1",
    "daily_tplus7",
    "weekly",
    "monthly_gamma",
    "monthly_landing_14d",
    "monthly_landing_21d",
}


class JobExecutionError(Exception):
    """ジョブ実行エラー"""
    pass


def validate_job_type(job_type: str) -> None:
    """
    job_type がホワイトリストに含まれるか検証
    
    Args:
        job_type: ジョブタイプ
    
    Raises:
        JobExecutionError: ホワイトリストに無いジョブタイプ
    """
    if job_type not in ALLOWED_JOB_TYPES:
        raise JobExecutionError(
            f"Job type '{job_type}' is not allowed. "
            f"Allowed types: {', '.join(sorted(ALLOWED_JOB_TYPES))}"
        )


def execute_daily_tplus1(
    db_session: Session,
    target_date: date,
    job_id: UUID,
    timeout: Optional[int] = None,
    use_training: bool = True,  # Phase 4: デフォルトで学習込み
) -> None:
    """
    日次予測 t+1 を実行
    
    Args:
        db_session: SQLAlchemy Session
        target_date: 予測対象日
        job_id: ジョブID
        timeout: タイムアウト（秒）
        use_training: True=学習込み（retrain_and_eval）, False=推論のみ
    
    Raises:
        JobExecutionError: 実行エラー
    """
    timeout = timeout or DEFAULT_TIMEOUT
    
    if use_training:
        # Phase 4: DB→学習→予測の完全フロー
        logger.info(f"🔄 Using training mode (retrain_and_eval --quick)")
        
        # Adapters をインポート（worker内にコピー済み）
        from .adapters.forecast.inbound_actuals_exporter import InboundActualsExporter
        from .adapters.forecast.reserve_exporter import ReserveExporter
        from .adapters.forecast.daily_forecast_result_repository import DailyForecastResultRepository
        
        # Adapters作成
        inbound_actuals_exporter = InboundActualsExporter(db_session)
        reserve_exporter = ReserveExporter(db_session)
        forecast_result_repo = DailyForecastResultRepository(db_session)
        
        # retrain_and_eval.py のパス
        retrain_script = SCRIPTS_DIR / "retrain_and_eval.py"
        if not retrain_script.exists():
            raise JobExecutionError(f"retrain_and_eval.py not found: {retrain_script}")
        
        # UseCase作成
        use_case = RunDailyTplus1ForecastWithTrainingUseCase(
            db_session=db_session,
            inbound_actuals_exporter=inbound_actuals_exporter,
            reserve_exporter=reserve_exporter,
            forecast_result_repo=forecast_result_repo,
            retrain_script_path=retrain_script,
            timeout=timeout,
        )
        
        # 実行
        try:
            use_case.execute(target_date, job_id)
            db_session.commit()
            
            logger.info(
                f"✅ Daily t+1 forecast (with training) completed and committed",
                extra={
                    "target_date": str(target_date),
                    "job_id": str(job_id)
                }
            )
        except Exception as e:
            db_session.rollback()
            logger.error(
                f"❌ Daily t+1 forecast (with training) failed",
                exc_info=True,
                extra={
                    "target_date": str(target_date),
                    "job_id": str(job_id),
                    "error": str(e)
                }
            )
            raise JobExecutionError(f"UseCase execution failed: {str(e)}") from e
    
    else:
        # Phase 3: 推論のみ（既存実装）
        logger.info(f"🔍 Using inference-only mode (existing model)")
        
        # モデルファイルパス
        model_bundle = MODELS_DIR / "final_fast_balanced" / "model_bundle.joblib"
        res_walk_csv = MODELS_DIR / "final_fast_balanced" / "res_walkforward.csv"
        script_path = SCRIPTS_DIR / "daily_tplus1_predict.py"
        
        # ファイル存在確認
        if not model_bundle.exists():
            raise JobExecutionError(f"Model bundle not found: {model_bundle}")
        if not res_walk_csv.exists():
            raise JobExecutionError(f"Walk-forward results not found: {res_walk_csv}")
        if not script_path.exists():
            raise JobExecutionError(f"Script not found: {script_path}")
        
        # Repositories を作成
        inbound_actual_repo = PostgreSQLInboundActualRepository(db_session)
        reserve_daily_repo = PostgreSQLReserveDailyRepository(db_session)
        forecast_result_repo = PostgreSQLForecastResultRepository(db_session)
        
        # UseCase を作成
        use_case = RunDailyTplus1ForecastUseCase(
            inbound_actual_repo=inbound_actual_repo,
            reserve_daily_repo=reserve_daily_repo,
            forecast_result_repo=forecast_result_repo,
            model_bundle_path=model_bundle,
            res_walk_csv_path=res_walk_csv,
            script_path=script_path,
            timeout=timeout,
        )
        
        # 実行
        try:
            use_case.execute(target_date, job_id)
            db_session.commit()
            
            logger.info(
                f"✅ Daily t+1 forecast (inference-only) completed and committed",
                extra={
                    "target_date": str(target_date),
                    "job_id": str(job_id)
                }
            )
        except Exception as e:
            db_session.rollback()
            logger.error(
                f"❌ Daily t+1 forecast (inference-only) failed",
                exc_info=True,
                extra={
                    "target_date": str(target_date),
                    "job_id": str(job_id),
                    "error": str(e)
                }
            )
            raise JobExecutionError(f"UseCase execution failed: {str(e)}") from e


def execute_job(
    db_session: Session,
    job_type: str,
    target_date: date,
    job_id: UUID,
    input_snapshot: dict,
    timeout: Optional[int] = None
) -> None:
    """
    ジョブを実行
    
    Args:
        db_session: SQLAlchemy Session
        job_type: ジョブタイプ
        target_date: 予測対象日
        job_id: ジョブID
        input_snapshot: 入力パラメータ
        timeout: タイムアウト（秒）
    
    Raises:
        JobExecutionError: 実行エラー
    """
    # ホワイトリスト検証
    validate_job_type(job_type)
    
    # job_type に応じた実行
    if job_type == "daily_tplus1":
        execute_daily_tplus1(db_session, target_date, job_id, timeout)
    else:
        # Phase 3では daily_tplus1 のみ実装
        raise JobExecutionError(
            f"Job type '{job_type}' is whitelisted but not yet implemented"
        )
