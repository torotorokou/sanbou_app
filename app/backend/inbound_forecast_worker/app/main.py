"""
Inbound Forecast Worker Entry Point
====================================
Purpose: 搬入量予測ジョブの非同期実行基盤

Phase 1: 起動確認（最小実装）
- 起動ログ出力
- 無限ループで生存維持
- SIGTERM でのグレースフルシャットダウン

Phase 2（次回）: ジョブポーリング実装
- DB から実行待ちジョブを取得
- 予測スクリプト実行
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
    Worker メインループ（Phase 1: 最小実装）
    
    Phase 1:
        - 起動確認用の heartbeat ログのみ
        - 60秒ごとにログ出力
    
    Phase 2（次回実装）:
        - ジョブポーリング実装
        - 予測スクリプト実行
    """
    logger.info("🚀 Inbound forecast worker started (Phase 1: Boot test)")
    logger.info("Worker is in standby mode - waiting for job polling implementation")
    
    heartbeat_counter = 0
    
    while not _shutdown_requested:
        heartbeat_counter += 1
        logger.debug(
            f"💓 Worker heartbeat #{heartbeat_counter}",
            extra={"heartbeat_count": heartbeat_counter}
        )
        
        # Phase 2 で以下を実装:
        # 1. DB から job を SELECT ... FOR UPDATE SKIP LOCKED
        # 2. 予測スクリプトを subprocess で実行（ホワイトリスト検証）
        # 3. 結果を DB に保存
        
        time.sleep(60)
    
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
