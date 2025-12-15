"""
Dependency Injection Providers

UseCaseとRepositoryの実装を組み立て、DIコンテナとして提供する。
環境差分の吸収もここで行う。
"""
import os
from pathlib import Path
from typing import Optional

from app.core.usecases.execute_daily_forecast_uc import ExecuteDailyForecastUseCase
from app.infra.adapters.prediction.script_executor import ScriptBasedPredictionExecutor


def get_scripts_dir() -> Path:
    """
    スクリプトディレクトリのパスを取得。
    
    Returns:
        Path: scriptsディレクトリのパス
    """
    # 環境変数から取得、デフォルトは /backend/app/infra/scripts
    scripts_dir = os.getenv("SCRIPTS_DIR", "/backend/app/infra/scripts")
    return Path(scripts_dir)


def get_db_connection_string() -> Optional[str]:
    """
    DB接続文字列を取得。
    
    Returns:
        Optional[str]: DB接続文字列（環境変数から取得）
    """
    return os.getenv("DATABASE_URL")


def get_prediction_executor() -> ScriptBasedPredictionExecutor:
    """
    PredictionExecutorの実装を取得。
    
    Returns:
        ScriptBasedPredictionExecutor: スクリプトベースの実装
    """
    scripts_dir = get_scripts_dir()
    db_connection_string = get_db_connection_string()
    enable_db_save = os.getenv("ENABLE_DB_SAVE", "true").lower() == "true"
    
    return ScriptBasedPredictionExecutor(
        scripts_dir=scripts_dir,
        db_connection_string=db_connection_string,
        enable_db_save=enable_db_save,
    )


def get_execute_daily_forecast_usecase() -> ExecuteDailyForecastUseCase:
    """
    ExecuteDailyForecastUseCaseを取得。
    
    Returns:
        ExecuteDailyForecastUseCase: 日次予測UseCaseのインスタンス
    """
    prediction_executor = get_prediction_executor()
    return ExecuteDailyForecastUseCase(prediction_executor=prediction_executor)
