"""スタートアップスクリプト

Git管理されたローカルファイルを使用するため、GCS同期機能は削除済み。
マスターデータとテンプレートは app/infra/data_sources/ に配置。
"""

from __future__ import annotations

from .settings import settings


def log(msg: str) -> None:
    print(f"[startup] {msg}", flush=True)


def main() -> None:
    stage = settings.stage
    log(f"stage={stage}: Git管理されたローカルファイルを使用")


if __name__ == "__main__":
    main()
