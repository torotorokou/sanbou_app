"""共通スタートアップスクリプト (preflight 統合版)

stg / prod いずれの環境でも利用できるよう、以下を行う:
1. (STRICT_STARTUP=true の場合含む) GCS / 認証 preflight を実施
     - サービスアカウント key ファイル存在 & JSON 解析
     - 対象バケット存在確認 & list_blobs 疎通
2. 環境変数 STAGE (dev|stg|prod) を参照 (なければ dev 扱い)
3. GCS バケット (環境別) から ledger_api 用の master / templates ディレクトリを同期
4. 取得したファイルは /backend/app/st_app/data 配下へ配置
5. エラーはロギングして継続 (STRICT_STARTUP=true 指定で例外化)

期待する環境変数:
    STAGE=stg|prod
    GCS_LEDGER_BUCKET_STG=gs://sanbouapp-stg/ledger_api/st_app
    GCS_LEDGER_BUCKET_PROD=gs://sanbouapp-prod/ledger_api/st_app
    (任意) GCS_LEDGER_BUCKET=gs://<override>/ledger_api/st_app
    GOOGLE_APPLICATION_CREDENTIALS=/backend/secrets/<key>.json
任意:
    STARTUP_DOWNLOAD_ENABLE=true (明示的に true の場合のみ実行。未設定なら stg/prod は実行、dev はスキップ)
    STRICT_STARTUP=true  失敗時に例外化
"""
from __future__ import annotations
import os
import json
import traceback
from pathlib import Path
from typing import Optional

from .settings import settings  # 新しい設定モジュール

try:  # 例外型参照用 (存在しない場合はダミー)
    from google.api_core.exceptions import NotFound as GCSNotFound  # type: ignore
except Exception:  # pragma: no cover
    class GCSNotFound(Exception):  # type: ignore
        pass

try:
    from google.cloud import storage  # type: ignore
except Exception:  # pragma: no cover - optional
    storage = None  # type: ignore

DATA_DIR = settings.data_dir
TARGET_SUBDIRS = settings.ledger_sync_subdirs


def log(msg: str) -> None:
    print(f"[startup] {msg}", flush=True)


def should_run() -> bool:
    return settings.should_download()


def bucket_base() -> Optional[str]:
    base = settings.bucket_base()
    # 旧挙動と互換: デフォルト値を補完
    if base is None:
        if settings.stage == "stg":
            return "gs://sanbouapp-stg/ledger_api/st_app"
        if settings.stage == "prod":
            return "gs://sanbouapp-prod/ledger_api/st_app"
    return base


def download() -> None:
    if storage is None:
        log("google-cloud-storage 未インストールのためスキップ")
        return

    base = bucket_base()
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
        except GCSNotFound as e:  # type: ignore
            log(f"  prefix取得で NotFound: {e!r}")
            continue
        except Exception as e:  # noqa: BLE001
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


# ------------------------------------------------------------
# Preflight (旧 startup_preflight.py の統合)
# ------------------------------------------------------------
def preflight(strict: bool) -> None:
    """GCS アクセス前の簡易チェック。

    - GOOGLE_APPLICATION_CREDENTIALS 指定ファイルの存在 & JSON 解析
    - 使用予定バケットの存在 (exists) & list_blobs(1) 疎通
    失敗時:
      strict=True -> 例外送出
      strict=False -> ログ警告のみ
    """
    cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred or not Path(cred).is_file():
        msg = f"key file missing: {cred}" if cred else "key file env not set"
        if strict:
            raise RuntimeError(msg)
        log(f"preflight warn: {msg}")
        return
    try:
        with open(cred, "r", encoding="utf-8") as f:
            ce = json.load(f).get("client_email")
        log(f"preflight: key client_email={ce}")
    except Exception as e:  # noqa: BLE001
        if strict:
            raise RuntimeError(f"parse key failed: {e!r}") from e
        log(f"preflight warn: parse key failed: {e!r}")
        return

    base = bucket_base()
    if not base or not base.startswith("gs://"):
        log("preflight: bucket base 未設定 / 不正 URL -> skip")
        return
    bucket_name = base[5:].split("/", 1)[0]
    if storage is None:
        log("preflight: google-cloud-storage 未インストール -> skip")
        return
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        if not bucket.exists():  # requires buckets.get or returns False
            msg = f"bucket not accessible (exists()=False): {bucket_name}"
            if strict:
                raise RuntimeError(msg)
            log(f"preflight warn: {msg}")
            return
        log(f"preflight: bucket exists OK: {bucket_name}")
        try:
            it = client.list_blobs(bucket_name, max_results=1)
            next(iter(it), None)
            log("preflight: list_blobs OK")
        except Exception as e:  # noqa: BLE001
            if strict:
                raise RuntimeError(f"list_blobs failed: {e!r}") from e
            log(f"preflight warn: list_blobs failed: {e!r}")
    except Exception as e:  # noqa: BLE001
        if strict:
            raise
        log(f"preflight warn: unexpected error: {e!r}")


def main() -> None:
    stage = settings.stage
    strict = settings.strict_startup

    # 統合 preflight
    try:
        preflight(strict)
    except Exception as e:  # pragma: no cover
        log("preflight エラー: " + repr(e))
        traceback.print_exc()
        if strict:
            raise
        else:
            log("STRICT_STARTUP=false のため継続")

    if not should_run():
        log(f"stage={stage}: ダウンロードスキップ (reason={settings.should_download_reason()})")
        return

    log(f"stage={stage}: データ同期開始 (reason={settings.should_download_reason()})")
    try:
        download()
        log("同期完了")
    except Exception as e:  # pragma: no cover
        log("エラー発生: " + repr(e))
        traceback.print_exc()
        if strict:
            raise
        else:
            log("STRICT_STARTUP=false のため継続")


if __name__ == "__main__":
    main()
