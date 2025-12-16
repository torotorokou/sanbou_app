"""
Job Executor for Forecast Worker
=================================
Purpose: job_type に応じて適切な予測スクリプトを実行

セキュリティ:
- ホワイトリスト方式：許可されたコマンドのみ実行
- 入力検証：job_type, target_date の妥当性チェック
- タイムアウト設定：長時間実行の防止

実行モデル:
1. daily_tplus1: 日次予測 t+1
   - スクリプト: scripts/daily_tplus1_predict.py
   - 入力: model_bundle.joblib, res_walkforward.csv
   - 出力: output/tplus1_pred_{target_date}.csv
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

from backend_shared.application.logging import get_module_logger

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
    target_date: date,
    timeout: Optional[int] = None
) -> str:
    """
    日次予測 t+1 を実行
    
    Args:
        target_date: 予測対象日
        timeout: タイムアウト（秒）
    
    Returns:
        str: 出力CSVファイルパス
    
    Raises:
        JobExecutionError: 実行エラー
    """
    timeout = timeout or DEFAULT_TIMEOUT
    
    # 出力ファイルパス
    output_csv = OUTPUT_DIR / f"tplus1_pred_{target_date.isoformat()}.csv"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # モデルファイルパス（デフォルト）
    model_bundle = MODELS_DIR / "final_fast_balanced" / "model_bundle.joblib"
    res_walk_csv = MODELS_DIR / "final_fast_balanced" / "res_walkforward.csv"
    
    # モデルファイル存在確認
    if not model_bundle.exists():
        raise JobExecutionError(f"Model bundle not found: {model_bundle}")
    if not res_walk_csv.exists():
        raise JobExecutionError(f"Walk-forward results not found: {res_walk_csv}")
    
    # コマンド構築
    script_path = SCRIPTS_DIR / "daily_tplus1_predict.py"
    if not script_path.exists():
        raise JobExecutionError(f"Script not found: {script_path}")
    
    cmd = [
        "python3",
        str(script_path),
        "--bundle", str(model_bundle),
        "--res-walk-csv", str(res_walk_csv),
        "--out-csv", str(output_csv),
        "--start-date", target_date.isoformat(),
    ]
    
    logger.info(
        f"Executing daily_tplus1 prediction",
        extra={
            "target_date": str(target_date),
            "command": " ".join(cmd),
            "timeout": timeout
        }
    )
    
    try:
        # subprocess 実行
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd="/backend"
        )
        
        # stdout/stderr をログに記録
        if result.stdout:
            logger.info(
                "Script stdout",
                extra={"stdout": result.stdout[:1000]}  # 最初の1000文字のみ
            )
        if result.stderr:
            logger.warning(
                "Script stderr",
                extra={"stderr": result.stderr[:1000]}
            )
        
        # リターンコードチェック
        if result.returncode != 0:
            raise JobExecutionError(
                f"Script exited with code {result.returncode}. "
                f"stderr: {result.stderr[:500]}"
            )
        
        # 出力ファイル存在確認
        if not output_csv.exists() or output_csv.stat().st_size == 0:
            raise JobExecutionError(
                f"Output file not created or empty: {output_csv}"
            )
        
        logger.info(
            f"✅ Prediction completed successfully",
            extra={
                "target_date": str(target_date),
                "output_file": str(output_csv),
                "file_size": output_csv.stat().st_size
            }
        )
        
        return str(output_csv)
        
    except subprocess.TimeoutExpired:
        raise JobExecutionError(
            f"Script execution timed out after {timeout} seconds"
        )
    except Exception as e:
        raise JobExecutionError(f"Unexpected error: {str(e)}") from e


def execute_job(
    job_type: str,
    target_date: date,
    input_snapshot: dict,
    timeout: Optional[int] = None
) -> str:
    """
    ジョブを実行
    
    Args:
        job_type: ジョブタイプ
        target_date: 予測対象日
        input_snapshot: 入力パラメータ
        timeout: タイムアウト（秒）
    
    Returns:
        str: 出力ファイルパス
    
    Raises:
        JobExecutionError: 実行エラー
    """
    # ホワイトリスト検証
    validate_job_type(job_type)
    
    # job_type に応じた実行
    if job_type == "daily_tplus1":
        return execute_daily_tplus1(target_date, timeout)
    else:
        # Phase 3では daily_tplus1 のみ実装
        raise JobExecutionError(
            f"Job type '{job_type}' is whitelisted but not yet implemented"
        )
