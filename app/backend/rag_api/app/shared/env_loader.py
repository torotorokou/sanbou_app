"""
環境変数ローダー

優先順に .env と secrets をロードして環境変数を設定する。

優先順:
1) CONFIG_ENV (.env) 既存の設定
2) SECRETS_DIR/.env.local_<STAGE>.secrets
3) SECRETS_DIR/.env.<STAGE>.secrets
4) SECRETS_DIR/.env.local.secrets
5) SECRETS_DIR/.env.secrets

STAGE は環境変数から取得（未設定時は dev）。
SECRETS_DIR 未設定時は /backend/secrets。
"""

from __future__ import annotations

import os
from pathlib import Path

from app.config.paths import CONFIG_ENV
from dotenv import load_dotenv


def load_env_and_secrets() -> str | None:
    """
    CONFIG_ENV とステージ別 secrets を読み込む。

    Returns:
        読み込んだ secrets ファイルパス（見つからなければ None）
    """
    # 1) 既存の .env を先にロード（override=False で既存値を保持）
    try:
        load_dotenv(dotenv_path=str(CONFIG_ENV), override=False)
    except Exception:
        pass

    # 2) ステージ別 secrets の探索
    stage = os.environ.get("STAGE") or os.environ.get("NODE_ENV") or "dev"
    secrets_dir = Path(os.environ.get("SECRETS_DIR", "/backend/secrets"))

    candidates = [
        secrets_dir / f".env.local_{stage}.secrets",
        secrets_dir / f".env.{stage}.secrets",
        secrets_dir / ".env.local.secrets",
        secrets_dir / ".env.secrets",
    ]

    for p in candidates:
        try:
            if p.exists():
                load_dotenv(dotenv_path=str(p), override=True)
                os.environ["SECRETS_LOADED_FROM"] = str(p)
                return str(p)
        except Exception:
            # secrets 読み込み失敗は致命的ではない
            continue
    return None
