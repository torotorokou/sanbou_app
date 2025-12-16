"""
Inbound Forecast Worker Entry Point
====================================
Purpose: 搬入量予測ジョブの非同期実行基盤

Phase 3 (Current): ジョブ実行実装完了
- 5秒ごとに forecast.forecast_jobs テーブルをポーリング
- SELECT ... FOR UPDATE SKIP LOCKED でジョブをクレーム
- ステータスを 'queued' → 'running' に更新
- job_type に応じた予測スクリプト実行
  * daily_tplus1: scripts/daily_tplus1_predict.py を subprocess 実行
  * ホワイトリスト検証（許可されたジョブタイプのみ実行）
  * タイムアウト設定（30分）
- 実行結果に応じてステータス更新（succeeded/failed）
"""
from __future__ import annotations

import signal
import sys
import time
from typing import NoReturn

# ==========================================
# 統合ロギング設定（backend_shared）
# ==========================================
from backend_shared.application.logging import get_module_logger, setup_logging

# ==========================================
# Worker モジュール
# ==========================================
from .db import get_db_session
from .job_executor import JobExecutionError, execute_job
from .job_poller import claim_next_job, mark_job_failed, mark_job_succeeded

# ==========================================
# ロギング初期化
# ==========================================
setup_logging()
logger = get_module_logger(__name__)

# ==========================================
# グローバル状態管理
# ==========================================
_shutdown_requested = False


def signal_handler(signum: int, frame) -> None:
    """
    SIGTERM/SIGINT ハンドラ
    
    Args:
        signum: シグナル番号
        frame: フレームオブジェクト
    """
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name}, initiating graceful shutdown...")
    _shutdown_requested = True


def worker_loop() -> NoReturn:
    """
    Worker メインループ（Phase 3: ジョブ実行実装完了）
    
    処理フロー:
    1. 5秒ごとに forecast.forecast_jobs テーブルをポーリング
    2. queued ジョブを1件クレーム（SELECT FOR UPDATE SKIP LOCKED）
    3. ジョブ実行（job_type に応じた予測スクリプト実行）
    4. 実行結果に応じてステータス更新（succeeded/failed）
    5. エラー時はリトライ（attempt < max_attempt の場合）
    """
    logger.info("🚀 Inbound forecast worker started (Phase 3: Job execution)")
    logger.info("Polling interval: 5 seconds")
    
    poll_counter = 0
    
    while not _shutdown_requested:
        poll_counter += 1
        
        try:
            with get_db_session() as db:
                # ジョブをクレーム
                job = claim_next_job(db)
                
                if job is None:
                    # ジョブが無い場合は静かにスキップ
                    logger.debug(
                        f"💤 Poll #{poll_counter}: No jobs available",
                        extra={"poll_count": poll_counter}
                    )
                else:
                    # ジョブをクレームした
                    logger.info(
                        f"🎯 Poll #{poll_counter}: Job claimed",
                        extra={
                            "poll_count": poll_counter,
                            "job_id": str(job["id"]),
                            "job_type": job["job_type"],
                            "target_date": str(job["target_date"])
                        }
                    )
                    
                    # Phase 3: ジョブ実行
                    try:
                        output_path = execute_job(
                            job_type=job["job_type"],
                            target_date=job["target_date"],
                            input_snapshot=job["input_snapshot"],
                            timeout=1800  # 30分
                        )
                        
                        logger.info(
                            f"✅ Job execution succeeded",
                            extra={
                                "job_id": str(job["id"]),
                                "output_path": output_path
                            }
                        )
                        
                        mark_job_succeeded(db, job["id"])
                        
                    except JobExecutionError as e:
                        # 実行エラー
                        error_msg = str(e)
                        logger.error(
                            f"❌ Job execution failed",
                            exc_info=True,
                            extra={
                                "job_id": str(job["id"]),
                                "job_type": job["job_type"],
                                "error": error_msg
                            }
                        )
                        
                        mark_job_failed(db, job["id"], error_msg, increment_attempt=True)
                        
                    except Exception as e:
                        # 予期しないエラー
                        error_msg = f"Unexpected error: {str(e)}"
                        logger.error(
                            f"❌ Unexpected error during job execution",
                            exc_info=True,
                            extra={
                                "job_id": str(job["id"]),
                                "error": error_msg
                            }
                        )
                        
                        mark_job_failed(db, job["id"], error_msg, increment_attempt=True)
                    
        except Exception as e:
            logger.error(
                "❌ Error in worker loop",
                exc_info=True,
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "poll_count": poll_counter
                }
            )
        
        # 5秒待機
        time.sleep(5)
    
    logger.info("✅ Worker shutdown complete")
    sys.exit(0)


def main() -> None:
    """Worker エントリポイント"""
    # シグナルハンドラ登録
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("=" * 60)
    logger.info("Inbound Forecast Worker")
    logger.info("=" * 60)
    
    try:
        worker_loop()
    except KeyboardInterrupt:
        logger.info("Worker stopped by keyboard interrupt")
        sys.exit(0)
    except Exception as e:
        logger.error(
            "❌ Worker fatal error",
            exc_info=True,
            extra={"error": str(e), "error_type": type(e).__name__}
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
