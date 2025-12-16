"""
Inbound Forecast Worker Entry Point
====================================
Purpose: 搬入量予測ジョブの非同期実行基盤

Phase 2 (Current): ジョブポーリング実装
- 5秒ごとに forecast.forecast_jobs テーブルをポーリング
- SELECT ... FOR UPDATE SKIP LOCKED でジョブをクレーム
- ステータスを 'queued' → 'running' に更新
- ジョブ実行（Phase 3で実装予定）

Phase 3 (Next): ジョブ実行実装
- job_type に応じた予測スクリプト実行
- subprocess でのホワイトリスト検証
- 結果の DB 保存
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
    Worker メインループ（Phase 2: ジョブポーリング実装）
    
    処理フロー:
    1. 5秒ごとに forecast.forecast_jobs テーブルをポーリング
    2. queued ジョブを1件クレーム（SELECT FOR UPDATE SKIP LOCKED）
    3. ジョブ実行（Phase 3で実装予定、現在はスタブ）
    4. 結果をDBに記録
    
    Phase 3（次回実装）:
        - job_type に応じた予測スクリプト実行
        - subprocess でのホワイトリスト検証
    """
    logger.info("🚀 Inbound forecast worker started (Phase 2: Job polling)")
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
                    
                    # Phase 3 で実装: ジョブ実行
                    # 現在はスタブ（すぐに成功としてマーク）
                    logger.warning(
                        "⚠️ Job execution not implemented yet (Phase 3)",
                        extra={"job_id": str(job["id"])}
                    )
                    
                    # 一旦成功としてマーク（Phase 3で実際の実行結果に応じて変更）
                    mark_job_succeeded(db, job["id"])
                    
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
