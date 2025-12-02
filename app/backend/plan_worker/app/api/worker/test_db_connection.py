from __future__ import annotations
import psycopg
from shared.config.settings import settings
from shared.logging.logger import get_logger
from backend_shared.application.logging import create_log_context

logger = get_logger(__name__)

def main():
    logger.info("接続テストを開始します...")
    try:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                logger.info("✅ PostgreSQLに接続成功!")
                logger.info(
                    "PostgreSQL version",
                    extra=create_log_context(version=version)
                )
    except Exception as e:
        logger.error("❌ 接続失敗: %s", e)

if __name__ == "__main__":
    main()
