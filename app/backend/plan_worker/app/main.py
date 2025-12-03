"""Simple worker entry point"""
from __future__ import annotations
import sys

# ==========================================
# 統一ロギング設定のインポート（backend_shared）
# ==========================================
from backend_shared.application.logging import setup_logging, get_module_logger

# ==========================================
# 統一ロギング設定の初期化
# ==========================================
# テクニカルログ基盤: JSON形式、Request ID付与、Uvicorn統合
# 環境変数 LOG_LEVEL で制御可能（DEBUG/INFO/WARNING/ERROR/CRITICAL）
setup_logging()
logger = get_module_logger(__name__)

def main():
    """Worker main entry point"""
    logger.info("Plan worker started")
    logger.info("Worker is in standby mode - waiting for implementation")
    
    # Keep container running
    import time
    while True:
        time.sleep(60)
        logger.debug("Worker heartbeat")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Worker error", exc_info=True, extra={"error": str(e)})
        sys.exit(1)
