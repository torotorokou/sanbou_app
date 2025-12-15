"""
Dependency Injection Providers

UseCaseとRepositoryの実装を組み立て、DIコンテナとして提供する。
環境差分の吸収もここで行う。
"""
import os
from pathlib import Path
from typing import Optional, Union

from app.core.usecases.execute_daily_forecast_uc import ExecuteDailyForecastUseCase
from app.infra.adapters.prediction.script_executor import ScriptBasedPredictionExecutor
from app.infra.adapters.prediction.service_executor import ServiceBasedPredictionExecutor


def get_model_bundle_path() -> Path:
    """
    モデルバンドルファイルのパスを取得。
    
    Returns:
        Path: model_bundle.joblibのパス
    """
    # 環境変数から取得、デフォルトは /backend/data/output/final_fast_balanced/model_bundle.joblib
    bundle_path = os.getenv(
        "MODEL_BUNDLE_PATH",
        "/backend/data/output/final_fast_balanced/model_bundle.joblib"
    )
    return Path(bundle_path)


def get_output_dir() -> Path:
    """
    出力ディレクトリのパスを取得。
    
    Returns:
        Path: 出力ディレクトリのパス
    """
    # 環境変数から取得、デフォルトは /backend/output
    output_dir = os.getenv("OUTPUT_DIR", "/backend/output")
    return Path(output_dir)


def get_res_walk_csv() -> Optional[Path]:
    """
    履歴CSVファイルのパスを取得。
    
    Returns:
        Optional[Path]: res_walkforward.csvのパス
    """
    # 環境変数から取得、デフォルトは /backend/data/output/final_fast_balanced/res_walkforward.csv
    res_walk_csv = os.getenv(
        "RES_WALK_CSV",
        "/backend/data/output/final_fast_balanced/res_walkforward.csv"
    )
    path = Path(res_walk_csv)
    return path if path.exists() else None


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


def get_prediction_executor() -> Union[ScriptBasedPredictionExecutor, ServiceBasedPredictionExecutor]:
    """
    PredictionExecutorの実装を取得。
    
    環境変数 EXECUTOR_TYPE で選択可能：
    - "service": ServiceBasedPredictionExecutor（推奨、高速、型安全）
    - "script": ScriptBasedPredictionExecutor（レガシー、subprocess）
    
    Returns:
        Union[ScriptBasedPredictionExecutor, ServiceBasedPredictionExecutor]: 実装
    """
    executor_type = os.getenv("EXECUTOR_TYPE", "service").lower()
    db_connection_string = get_db_connection_string()
    enable_db_save = os.getenv("ENABLE_DB_SAVE", "true").lower() == "true"
    
    if executor_type == "service":
        # ServiceBasedPredictionExecutor（新実装）
        model_bundle_path = get_model_bundle_path()
        output_dir = get_output_dir()
        res_walk_csv = get_res_walk_csv()
        
        return ServiceBasedPredictionExecutor(
            model_bundle_path=model_bundle_path,
            output_dir=output_dir,
            res_walk_csv=res_walk_csv,
            db_connection_string=db_connection_string,
            enable_db_save=enable_db_save,
        )
    else:
        # ScriptBasedPredictionExecutor（レガシー）
        scripts_dir = get_scripts_dir()
        
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
