#!/usr/bin/env python3
"""GCSから手動でマスターデータをダウンロードするスクリプト

⚠️ 重要: このスクリプトは開発環境専用です
   - 本番環境・Staging環境では使用しないでください
   - 本番・Stagingでは、各コンテナが backend_shared の GcsFileStorageRepository を
     使用して GCS から直接データを取得します
   - このスクリプトは、ローカル開発者が GCS に直接アクセスできない場合の
     ワークアラウンドとして提供されています

使用方法:
    python scripts/download_master_data.py

前提条件:
    - GOOGLE_APPLICATION_CREDENTIALS環境変数が設定されている
    - google-cloud-storageがインストールされている
    
推奨される方法:
    - 各コンテナで FILE_STORAGE_MODE=gcs を設定し、backend_shared の
      GcsFileStorageRepository 経由で直接 GCS にアクセスすることを推奨します
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
    """GCSからマスターデータとテンプレートをダウンロード"""
    
    # 認証確認
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not Path(cred_path).exists():
        print(f"ERROR: GOOGLE_APPLICATION_CREDENTIALS が設定されていないか、ファイルが存在しません: {cred_path}")
        exit(1)
    
    print(f"✓ 認証ファイル: {cred_path}")
    
    # GCSクライアント初期化
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        print(f"✓ バケット接続: gs://{BUCKET_NAME}")
    except Exception as e:
        print(f"ERROR: バケット接続失敗: {e}")
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


if __name__ == "__main__":
    download_from_gcs()
