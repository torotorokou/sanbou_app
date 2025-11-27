"""Simple worker entry point"""
from __future__ import annotations
import sys
from app.shared.logging.logger import get_logger

logger = get_logger(__name__)

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
        logger.error(f"Worker error: {e}", exc_info=True)
        sys.exit(1)
