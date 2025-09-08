"""共通スタートアップスクリプト

stg / prod いずれの環境でも利用できるよう、以下を行う:
1. 環境変数 STAGE (dev|stg|prod) を参照 (なければ dev 扱いでスキップ)
2. GCS バケット (環境別) から ledger_api 用の master / template ディレクトリを同期
3. 取得したファイルは /backend/app/st_app/data 配下へ配置
4. エラーはロギングして継続 (起動失敗を避けたい場合は STRICT_STARTUP=true 指定で例外化)

期待する環境変数:
  STAGE=stg|prod
  GCS_LEDGER_BUCKET_STG=gs://sanbouapp-stg/ledger_api/st_app
  GCS_LEDGER_BUCKET_PROD=gs://sanbouapp-prod/ledger_api/st_app
  GOOGLE_APPLICATION_CREDENTIALS=/backend/secrets/<key>.json
任意:
  STARTUP_DOWNLOAD_ENABLE=true (明示的に true の場合のみ実行。未設定なら stg/prod は実行、dev はスキップ)
  STRICT_STARTUP=true  失敗時に例外送出してコンテナクラッシュ
"""
from __future__ import annotations
import os
import traceback
from pathlib import Path
from typing import Optional

try:  # 例外型参照用 (存在しない場合はダミー)
    from google.api_core.exceptions import NotFound as GCSNotFound  # type: ignore
except Exception:  # pragma: no cover
    class GCSNotFound(Exception):  # type: ignore
        pass

try:
    from google.cloud import storage  # type: ignore
except Exception:  # pragma: no cover - optional
    storage = None  # type: ignore

DATA_DIR = Path("/backend/app/st_app/data")
TARGET_SUBDIRS = ["master", "templates"]


def log(msg: str) -> None:
    print(f"[startup] {msg}", flush=True)


def should_run(stage: str) -> bool:
    # dev はデフォルト実行しない
    env_flag = os.getenv("STARTUP_DOWNLOAD_ENABLE")
    if env_flag is not None:
        return env_flag.lower() in {"1", "true", "yes", "on"}
    return stage in {"stg", "prod"}


def bucket_base(stage: str) -> Optional[str]:
    """優先順位:
    1. 共通オーバーライド GCS_LEDGER_BUCKET (例: gs://my-bucket/ledger_api/st_app)
    2. ステージ別 GCS_LEDGER_BUCKET_<STAGE>
    3. デフォルト (stg/prod のみ)
    """
    override = os.getenv("GCS_LEDGER_BUCKET")
    if override:
        return override
    if stage == "stg":
        return os.getenv("GCS_LEDGER_BUCKET_STG", "gs://sanbouapp-stg/ledger_api/st_app")
    if stage == "prod":
        return os.getenv("GCS_LEDGER_BUCKET_PROD", "gs://sanbouapp-prod/ledger_api/st_app")
    return None


def download(stage: str) -> None:
    if storage is None:
        log("google-cloud-storage 未インストールのためスキップ")
        return

    base = bucket_base(stage)
    if not base:
        log("バケットベース未設定。スキップ")
        return

    # gs://bucket/path 形式を分解
    if not base.startswith("gs://"):
        log(f"不正な GCS URL: {base}")
        return
    parts = base[5:].split("/", 1)
    bucket_name = parts[0]
    prefix_root = parts[1] if len(parts) > 1 else ""

    client = storage.Client()  # 認証は GOOGLE_APPLICATION_CREDENTIALS に依存

    from google.api_core.exceptions import Forbidden as GCSForbidden  # type: ignore
    from google.api_core.exceptions import NotFound as GCSRealNotFound  # type: ignore

    bucket = None
    try:
        bucket = client.get_bucket(bucket_name)  # buckets.get 権限があれば成功
    except GCSForbidden as fe:
        msg = str(fe)
        if "storage.buckets.get" in msg:
            log("buckets.get 権限なし: メタ取得をスキップしてオブジェクト一覧のみで同期を試行")
            bucket = client.bucket(bucket_name)
        else:
            log(f"バケットアクセス Forbidden: {fe!r}")
            return
    except GCSRealNotFound:
        log(f"バケット '{bucket_name}' が存在しません")
        return

    if bucket is None:
        log("バケット参照取得に失敗したため同期をスキップ")
        return

    for sub in TARGET_SUBDIRS:
        # 🔽 修正: st_app 配下を探す
        prefix = f"{prefix_root}/data/{sub}" if prefix_root else f"st_app/data/{sub}"
        local_dir = DATA_DIR / sub
        local_dir.mkdir(parents=True, exist_ok=True)
        log(f"sync: gs://{bucket_name}/{prefix} -> {local_dir}")
        try:
            blobs = list(client.list_blobs(bucket, prefix=prefix))
        except GCSNotFound as e:
            log(f"  prefix取得で NotFound: {e!r}")
            continue
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                log(f"  オブジェクト一覧権限不足 (list_blobs 失敗): {e!r} -> 同期スキップ")
                continue
            raise
        if not blobs:
            log("  (no objects)")
            continue
        # ローカル既存ファイル削除
        for p in local_dir.glob("**/*"):
            if p.is_file():
                p.unlink()
        for b in blobs:
            rel = b.name[len(prefix):].lstrip("/")
            if not rel:
                continue
            dest = local_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            b.download_to_filename(dest)
            log(f"  downloaded {rel}")


def main() -> None:
    stage = os.getenv("STAGE", "dev").lower()
    if not should_run(stage):
        log(f"stage={stage}: ダウンロードスキップ")
        return

    log(f"stage={stage}: データ同期開始")
    try:
        download(stage)
        log("同期完了")
    except Exception as e:  # pragma: no cover
        log("エラー発生: " + repr(e))
        traceback.print_exc()
        if os.getenv("STRICT_STARTUP", "false").lower() in {"1", "true", "yes"}:
            raise
        else:
            log("STRICT_STARTUP=false のため継続")


if __name__ == "__main__":
    main()
