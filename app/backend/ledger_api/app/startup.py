"""スタートアップスクリプト

Git管理されたローカルファイルを使用するため、GCS同期機能は削除済み。
マスターデータとテンプレートは app/infra/data_sources/ に配置。
"""

from __future__ import annotations

from backend_shared.application.logging import get_module_logger

from .settings import settings


logger = get_module_logger(__name__)


def log(msg: str) -> None:
    logger.info(msg)


def main() -> None:
    stage = settings.stage
    log(f"stage={stage}: Git管理されたローカルファイルを使用")


if __name__ == "__main__":
    main()
