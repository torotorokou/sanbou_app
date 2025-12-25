"""Settings loader for ledger_api.

backend_shared の BaseAppSettings を継承し、ledger_api 固有の設定を追加します。
環境変数を一箇所で管理/変換し、他モジュールは `from app.settings import settings`
経由で参照する。

主な環境変数:
  STAGE=dev|stg|prod
  STRICT_STARTUP=true|false
  STARTUP_DOWNLOAD_ENABLE=true|false (明示 true の場合のみ有効)
  GCS_LEDGER_BUCKET=<gs://...> (全環境 override)
  GCS_LEDGER_BUCKET_STG=<gs://...>
  GCS_LEDGER_BUCKET_PROD=<gs://...>
  GCS_LEDGER_BUCKET_DEV=<gs://...>
  BASE_API_DIR=/backend/app/api (data/logs 配下算出に利用)
  LEDGER_SYNC_SUBDIRS=master,templates (カンマ区切り)
  REPORT_ARTIFACT_SECRET=<secret-key> (PDF署名用)
"""

from __future__ import annotations

import os
from pathlib import Path

from backend_shared.config.base_settings import BaseAppSettings

TRUE_SET = {"1", "true", "yes", "on"}


def _as_bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return val.lower() in TRUE_SET


class LedgerApiSettings(BaseAppSettings):
    """
    Ledger API 設定クラス

    BaseAppSettings を継承し、Ledger API 固有の設定を追加します。
    """

    # ========================================
    # API基本情報
    # ========================================

    API_TITLE: str = "帳票・日報API"
    API_VERSION: str = "1.0.0"

    # ========================================
    # Ledger API 固有設定
    # ========================================

    stage: str = ""
    strict_startup: bool = False
    startup_download_enable_raw: str | None = None
    base_api_dir: Path = Path("/backend/app/api")
    gcs_ledger_bucket_override: str | None = None
    gcs_ledger_bucket_dev: str | None = None
    gcs_ledger_bucket_stg: str | None = None
    gcs_ledger_bucket_prod: str | None = None
    ledger_sync_subdirs: list[str] = []
    report_artifact_root_dir: Path = Path("/backend/data/report_artifacts")
    report_artifact_url_prefix: str = "/api/report_artifacts"
    report_artifact_url_ttl: int = 900
    report_artifact_secret: str = (
        "change-me-in-production"  # デフォルトは insecure (環境変数で上書き必須)
    )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

    def bucket_base(self) -> str | None:
        if self.gcs_ledger_bucket_override:
            return self.gcs_ledger_bucket_override
        if self.stage == "dev":
            return self.gcs_ledger_bucket_dev
        if self.stage == "stg":
            return self.gcs_ledger_bucket_stg
        if self.stage == "prod":
            return self.gcs_ledger_bucket_prod
        return None

    @property
    def data_dir(self) -> Path:
        # データソースはinfra/data_sourcesに移動済み
        return self.base_api_dir.parent / "infra" / "data_sources"

    @property
    def logs_dir(self) -> Path:
        return self.base_api_dir / "logs"

    def should_download(self) -> bool:
        raw = self.startup_download_enable_raw
        # 空文字/空白のみは未指定扱い (compose で `VAR=` と書かれたケースを救済)
        if raw is not None and raw.strip() == "":
            raw = None
        if raw is not None:
            return _as_bool(raw, False)
        # dev環境ではGit管理されたローカルファイルを使用するため、デフォルトでGCS同期しない
        # stg/prodのみGCS同期を実行
        return self.stage in {"stg", "prod"}

    def should_download_reason(self) -> str:
        raw = self.startup_download_enable_raw
        if raw is not None and raw.strip() == "":
            raw = None
        if raw is not None:
            return f"STARTUP_DOWNLOAD_ENABLE explicitly set -> {_as_bool(raw, False)}"
        return f"stage={self.stage} default policy -> {self.stage in {'stg','prod'}}"


def load_settings() -> LedgerApiSettings:
    stage = os.getenv("STAGE", "dev").lower()
    strict_startup = _as_bool(os.getenv("STRICT_STARTUP"), False)
    startup_download_enable_raw = os.getenv("STARTUP_DOWNLOAD_ENABLE")
    base_api_dir = Path(os.getenv("BASE_API_DIR", "/backend/app/api"))

    def _clean(val: str | None) -> str | None:
        if val is None:
            return None
        v = val.strip()
        if not v:
            return None
        # env_file の後置コメント誤認 (例: VAR= # comment) を検出
        if v.startswith("#"):
            return None
        return v

    gcs_ledger_bucket_override = _clean(os.getenv("GCS_LEDGER_BUCKET"))
    gcs_ledger_bucket_dev = _clean(os.getenv("GCS_LEDGER_BUCKET_DEV"))
    gcs_ledger_bucket_stg = _clean(os.getenv("GCS_LEDGER_BUCKET_STG"))
    gcs_ledger_bucket_prod = _clean(os.getenv("GCS_LEDGER_BUCKET_PROD"))
    subdirs_raw = os.getenv("LEDGER_SYNC_SUBDIRS", "master,templates").strip()
    ledger_sync_subdirs = [s.strip() for s in subdirs_raw.split(",") if s.strip()]

    # presentation/static/reports をデフォルトのアーティファクト保存先とする
    artifact_root_default = base_api_dir.parent / "presentation" / "static"
    report_artifact_root_dir = Path(
        os.getenv("REPORT_ARTIFACT_ROOT_DIR", str(artifact_root_default))
    ).resolve()

    # アーティファクトURL生成用の内部論理パス
    # BFF(core_api)が外向きプレフィックス(/core_api)を担保するため、
    # ledger_apiは内部論理パス(/reports/artifacts)のみを知る（DIP: 依存関係逆転）
    report_artifact_url_prefix = (
        os.getenv(
            "REPORT_ARTIFACT_URL_PREFIX",
            "/reports/artifacts",  # デフォルトは内部論理パス
        ).strip()
        or "/reports/artifacts"
    )

    report_artifact_url_ttl_raw = os.getenv("REPORT_ARTIFACT_URL_TTL", "900")
    try:
        report_artifact_url_ttl = int(report_artifact_url_ttl_raw)
    except ValueError:
        report_artifact_url_ttl = 900

    # PDF署名用のシークレットキーを環境変数から取得
    report_artifact_secret = os.getenv(
        "REPORT_ARTIFACT_SECRET", "change-me-in-production"
    ).strip()

    _settings = LedgerApiSettings(
        stage=stage,
        strict_startup=strict_startup,
        startup_download_enable_raw=startup_download_enable_raw,
        base_api_dir=base_api_dir,
        gcs_ledger_bucket_override=gcs_ledger_bucket_override,
        gcs_ledger_bucket_dev=gcs_ledger_bucket_dev,
        gcs_ledger_bucket_stg=gcs_ledger_bucket_stg,
        gcs_ledger_bucket_prod=gcs_ledger_bucket_prod,
        ledger_sync_subdirs=ledger_sync_subdirs,
        report_artifact_root_dir=report_artifact_root_dir,
        report_artifact_url_prefix=report_artifact_url_prefix,
        report_artifact_url_ttl=report_artifact_url_ttl,
        report_artifact_secret=report_artifact_secret,
    )

    # セキュリティチェック: insecure なデフォルト値のまま起動していないか確認
    secret = _settings.report_artifact_secret
    is_insecure = secret in ("", "change-me-in-production")
    is_weak = len(secret) < 32

    if stage in {"stg", "prod"}:
        # 本番/ステージング環境では強制チェック（起動を停止）
        if is_insecure:
            raise ValueError(
                "🔴 SECURITY ERROR: REPORT_ARTIFACT_SECRET is using insecure default value!\n"
                "PDF signature security is compromised.\n"
                "Generate a strong secret: openssl rand -base64 32\n"
                f"Set it in: secrets/.env.{stage}.secrets"
            )
        if is_weak:
            raise ValueError(
                "🔴 SECURITY ERROR: REPORT_ARTIFACT_SECRET must be at least 32 characters!\n"
                f"Current length: {len(secret)}\n"
                "Generate a strong secret: openssl rand -base64 32\n"
                f"Set it in: secrets/.env.{stage}.secrets"
            )

        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            "✅ REPORT_ARTIFACT_SECRET validated successfully",
            extra={
                "operation": "load_settings",
                "stage": stage,
                "secret_length": len(secret),
            },
        )
    else:
        # 開発環境では警告のみ
        if is_insecure or is_weak:
            print(
                f"⚠️  WARNING: REPORT_ARTIFACT_SECRET is weak (length: {len(secret)})\n"
                "   This is OK for development, but MUST be set in production!\n"
                "   Generate: openssl rand -base64 32"
            )

    return _settings


settings = load_settings()

__all__ = ["settings", "LedgerApiSettings"]
