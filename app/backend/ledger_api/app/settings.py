"""Settings loader for ledger_api.

環境変数を一箇所で管理/変換し、他モジュールは `from app.settings import settings`
経由で参照する。依存ライブラリを増やさないため pydantic などは未使用。

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
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import List, Optional


TRUE_SET = {"1", "true", "yes", "on"}


def _as_bool(val: Optional[str], default: bool = False) -> bool:
    if val is None:
        return default
    return val.lower() in TRUE_SET


@dataclass(slots=True)
class Settings:
    stage: str
    strict_startup: bool
    startup_download_enable_raw: Optional[str]
    base_api_dir: Path
    gcs_ledger_bucket_override: Optional[str]
    gcs_ledger_bucket_dev: Optional[str]
    gcs_ledger_bucket_stg: Optional[str]
    gcs_ledger_bucket_prod: Optional[str]
    ledger_sync_subdirs: List[str]
    report_artifact_root_dir: Path
    report_artifact_url_prefix: str
    report_artifact_url_ttl: int
    report_artifact_secret: str

    def bucket_base(self) -> Optional[str]:
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


def load_settings() -> Settings:
    stage = os.getenv("STAGE", "dev").lower()
    strict_startup = _as_bool(os.getenv("STRICT_STARTUP"), False)
    startup_download_enable_raw = os.getenv("STARTUP_DOWNLOAD_ENABLE")
    base_api_dir = Path(os.getenv("BASE_API_DIR", "/backend/app/api"))
    def _clean(val: Optional[str]) -> Optional[str]:
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
    report_artifact_root_dir = Path(os.getenv("REPORT_ARTIFACT_ROOT_DIR", str(artifact_root_default))).resolve()
    
    # アーティファクトURL生成用の内部論理パス
    # BFF(core_api)が外向きプレフィックス(/core_api)を担保するため、
    # ledger_apiは内部論理パス(/reports/artifacts)のみを知る（DIP: 依存関係逆転）
    report_artifact_url_prefix = os.getenv(
        "REPORT_ARTIFACT_URL_PREFIX", 
        "/reports/artifacts"  # デフォルトは内部論理パス
    ).strip() or "/reports/artifacts"
    
    report_artifact_url_ttl_raw = os.getenv("REPORT_ARTIFACT_URL_TTL", "900")
    try:
        report_artifact_url_ttl = int(report_artifact_url_ttl_raw)
    except ValueError:
        report_artifact_url_ttl = 900
    
    # REPORT_ARTIFACT_SECRET: PDF生成署名用のシークレットキー
    # 注意: 本番環境では必ず強力なランダム文字列を設定すること
    report_artifact_secret = os.getenv("REPORT_ARTIFACT_SECRET")
    if not report_artifact_secret:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "REPORT_ARTIFACT_SECRET not set - using insecure default. "
            "This MUST be set in production!"
        )
        report_artifact_secret = "change-me-in-production"
    
    return Settings(
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


settings = load_settings()

__all__ = ["settings", "Settings"]
