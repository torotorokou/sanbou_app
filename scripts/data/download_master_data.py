#!/usr/bin/env python3
"""GCSから手動でマスターデータをダウンロードするスクリプト

使用方法:
    python scripts/download_master_data.py

前提条件:
    - ローカル環境: gcloud auth application-default login を実行済み
    - GCE環境: VMに適切な権限を持つサービスアカウントがアタッチされている
    - google-cloud-storageがインストールされている

認証方式:
    Application Default Credentials (ADC) を使用します。
    JSONキーファイルは不要です。
"""
import os
from pathlib import Path

try:
    from google.cloud import storage
except ImportError:
    print("ERROR: google-cloud-storage がインストールされていません")
    print("pip install google-cloud-storage を実行してください")
    exit(1)

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
TARGET_DIR = PROJECT_ROOT / "app" / "backend" / "ledger_api" / "app" / "infra" / "data_sources"

# GCS設定（環境に応じて変更）
BUCKET_NAME = "sanbouapp-dev"
GCS_PREFIX = "ledger_api/st_app/data"  # master/, templates/ を含むベースパス

TARGET_SUBDIRS = ["master", "templates"]


def download_from_gcs():
    """GCSからマスターデータとテンプレートをダウンロード

    ADC (Application Default Credentials) を使用してGCSに接続します。

    前提条件:
        - ローカル: gcloud auth application-default login を実行済み
        - GCE: VMにサービスアカウントがアタッチされている
    """

    # GCSクライアント初期化（ADCを使用）
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        print(f"✓ バケット接続（ADC使用）: gs://{BUCKET_NAME}")
    except Exception as e:
        print(f"ERROR: バケット接続失敗: {e}")
        print("\nヒント:")
        print("  - ローカル: gcloud auth application-default login を実行してください")
        print("  - GCE: VMに適切な権限を持つサービスアカウントがアタッチされているか確認してください")
        exit(1)

    # 各サブディレクトリをダウンロード
    for subdir in TARGET_SUBDIRS:
        prefix = f"{GCS_PREFIX}/{subdir}/"
        local_dir = TARGET_DIR / subdir

        print(f"\n📥 ダウンロード中: gs://{BUCKET_NAME}/{prefix} -> {local_dir}")

        # ローカルディレクトリ作成
        local_dir.mkdir(parents=True, exist_ok=True)

        # 既存ファイルを削除（クリーンアップ）
        for existing_file in local_dir.rglob("*"):
            if existing_file.is_file():
                existing_file.unlink()
                print(f"  🗑️  削除: {existing_file.relative_to(TARGET_DIR)}")

        # GCSからダウンロード
        blobs = list(client.list_blobs(BUCKET_NAME, prefix=prefix))

        if not blobs:
            print(f"  ⚠️  ファイルが見つかりません")
            continue

        downloaded_count = 0
        for blob in blobs:
            # プレフィックスからの相対パスを取得
            rel_path = blob.name[len(prefix):]
            if not rel_path:  # ディレクトリのみのケース
                continue

            dest_path = local_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            blob.download_to_filename(str(dest_path))
            print(f"  ✓ {rel_path}")
            downloaded_count += 1

        print(f"  合計: {downloaded_count} ファイル")

    print("\n✅ ダウンロード完了")
    print(f"\nダウンロード先: {TARGET_DIR}")
    print("\n次のステップ:")
    print("  1. ファイルを確認: ls -la app/backend/ledger_api/app/infra/data_sources/master/")
    print("  2. Git に追加: git add app/backend/ledger_api/app/infra/data_sources/")
    print("  3. コミット: git commit -m 'chore: Add master data and templates from GCS'")
    print("\n認証情報:")
    print("  - ADC (Application Default Credentials) を使用しました")


if __name__ == "__main__":
    download_from_gcs()
