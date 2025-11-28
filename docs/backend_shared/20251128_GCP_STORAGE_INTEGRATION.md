# Backend Shared - GCP Storage Integration

**日付**: 2025-11-28  
**リファクタリング**: GCP 共有機能の backend_shared への集約

---

## 概要

このドキュメントは、GCP（主に GCS）のデータアクセスを backend_shared に集約し、各バックエンドコンテナ（core_api / ledger_api / rag_api / バッチ等）から共通利用できるようにしたリファクタリングの内容を説明します。

## アーキテクチャ方針

### データアクセスルール

1. **フロントエンド → core_api 経由のみ**
   - フロントエンドは必ず core_api の API を経由してデータにアクセス
   - フロントエンドが直接 GCP / DB に接続するコードは禁止

2. **バックエンドコンテナ間 → GCP 直接アクセス**
   - 他のバックエンドコンテナ（ledger_api, rag_api, バッチ等）は、
     HTTP で core_api を叩かず、自身のコンテナ内から GCP SDK を使って GCP に直接アクセス
   - 実装は backend_shared を利用

3. **backend_shared の役割**
   - インフラ・ユーティリティ・共通ポートのみを提供
   - 各サービス固有のドメインや UseCase は持たない
   - 依存関係: 各コンテナ → backend_shared （一方向のみ）

---

## backend_shared の構造

```
backend_shared/
  src/backend_shared/
    core/
      ports/
        file_storage_port.py      # ファイルストレージ抽象ポート
    infra/
      storage/
        local_file_storage_repository.py   # ローカル実装
        gcs_file_storage_repository.py     # GCS実装
      gcp/
        # 将来的にBigQuery等の実装もここに追加可能
```

### FileStoragePort

ファイルストレージの抽象ポートで、以下のメソッドを提供：

- `read_bytes(path: str) -> bytes`: バイナリ読み込み
- `read_text(path: str, encoding: str) -> str`: テキスト読み込み
- `exists(path: str) -> bool`: 存在確認
- `list_files(prefix: str) -> List[str]`: ファイル一覧取得
- `write_bytes(path: str, content: bytes)`: バイナリ書き込み
- `write_text(path: str, content: str, encoding: str)`: テキスト書き込み

### LocalFileStorageRepository

ローカルファイルシステム用の実装。開発環境やテスト環境で使用。

**初期化パラメータ:**
- `base_dir`: ベースディレクトリ（全ての相対パスの起点）

### GcsFileStorageRepository

Google Cloud Storage 用の実装。本番環境や Staging 環境で使用。

**初期化パラメータ:**
- `bucket_name`: GCS バケット名（gs:// プレフィックスは不要）
- `base_prefix`: バケット内のベースプレフィックス（省略可）
- `credentials_path`: サービスアカウントキーのパス（省略時は環境変数から取得）

**依存パッケージ:**
- `google-cloud-storage>=2.10.0`

---

## core_api での利用方法

### 1. DI 設定（config/di_providers.py）

```python
from backend_shared.core.ports.file_storage_port import FileStoragePort
from backend_shared.infra.storage.local_file_storage_repository import LocalFileStorageRepository
from backend_shared.infra.storage.gcs_file_storage_repository import GcsFileStorageRepository

def get_file_storage() -> FileStoragePort:
    """FileStoragePort提供（環境変数で動的切替）"""
    mode = os.getenv("FILE_STORAGE_MODE", "local").lower()

    if mode == "gcs":
        bucket = os.getenv("FILE_STORAGE_GCS_BUCKET")
        base_prefix = os.getenv("FILE_STORAGE_GCS_BASE_PREFIX", "")
        credentials_path = os.getenv("FILE_STORAGE_GCS_CREDENTIALS")
        
        return GcsFileStorageRepository(
            bucket_name=bucket,
            base_prefix=base_prefix,
            credentials_path=credentials_path,
        )
    
    # default: local
    base_dir = Path(os.getenv("FILE_STORAGE_LOCAL_BASE_DIR", "/backend/data"))
    return LocalFileStorageRepository(base_dir=base_dir)
```

### 2. 環境変数

**共通:**
- `FILE_STORAGE_MODE`: "local" or "gcs" (default: "local")

**ローカルモード:**
- `FILE_STORAGE_LOCAL_BASE_DIR`: ベースディレクトリ (default: /backend/data)

**GCSモード:**
- `FILE_STORAGE_GCS_BUCKET`: バケット名 (required)
- `FILE_STORAGE_GCS_BASE_PREFIX`: ベースプレフィックス (optional)
- `FILE_STORAGE_GCS_CREDENTIALS`: 認証ファイルパス (optional, デフォルトは GOOGLE_APPLICATION_CREDENTIALS)

### 3. UseCase での利用

```python
from io import BytesIO
import pandas as pd
from backend_shared.core.ports.file_storage_port import FileStoragePort

class LoadInboundService:
    def __init__(self, storage: FileStoragePort) -> None:
        self._storage = storage

    def load_inbound_csv(self, path: str) -> pd.DataFrame:
        data = self._storage.read_bytes(path)
        return pd.read_csv(BytesIO(data))
```

### 4. Router での注入

```python
from fastapi import APIRouter, Depends
from backend_shared.core.ports.file_storage_port import FileStoragePort
from app.config.di_providers import get_file_storage

router = APIRouter(prefix="/inbound", tags=["inbound"])

@router.get("/summary")
def get_inbound_summary(
    storage: FileStoragePort = Depends(get_file_storage),
):
    usecase = GetInboundSummaryUseCase(storage=storage)
    return usecase.execute()
```

---

## ヘルスチェック API

core_api に追加されたストレージヘルスチェックエンドポイント：

**エンドポイント:** `GET /system/storage/health`

**クエリパラメータ:**
- `test_prefix`: テスト対象のプレフィックス（省略時はルート）

**レスポンス例:**
```json
{
  "status": "ok",
  "storage_type": "gcs",
  "test_prefix": "master",
  "can_list": true,
  "file_count": 42,
  "first_file": "master/category.csv",
  "first_file_exists": true
}
```

---

## 他のコンテナでの利用

### ledger_api の例

```python
# ledger_api/app/config/di_providers.py
from backend_shared.core.ports.file_storage_port import FileStoragePort
from backend_shared.infra.storage.gcs_file_storage_repository import GcsFileStorageRepository

def get_ledger_file_storage() -> FileStoragePort:
    """ledger_api 用 FileStorage"""
    bucket = os.environ["LEDGER_FILE_STORAGE_GCS_BUCKET"]
    base_prefix = os.getenv("LEDGER_FILE_STORAGE_GCS_BASE_PREFIX", "ledger_api/api")
    return GcsFileStorageRepository(bucket_name=bucket, base_prefix=base_prefix)
```

### rag_api の例

```python
# rag_api/app/config/di_providers.py
from backend_shared.core.ports.file_storage_port import FileStoragePort
from backend_shared.infra.storage.gcs_file_storage_repository import GcsFileStorageRepository

def get_rag_file_storage() -> FileStoragePort:
    """rag_api 用 FileStorage"""
    bucket = os.environ["RAG_FILE_STORAGE_GCS_BUCKET"]
    base_prefix = os.getenv("RAG_FILE_STORAGE_GCS_BASE_PREFIX", "rag_api/master")
    return GcsFileStorageRepository(bucket_name=bucket, base_prefix=base_prefix)
```

---

## GCS からのローカルダウンロード（開発専用）

### 注意事項

⚠️ **本番・Staging では使用しないでください**

- GCS → ローカル同期スクリプトは開発環境専用です
- 本番・Staging では、各コンテナが backend_shared の GcsFileStorageRepository を使用して GCS から直接データを取得します

### 開発環境でのスクリプト

**scripts/download_master_data.py:**
- ローカル開発者が GCS に直接アクセスできない場合のワークアラウンド
- 実行: `python scripts/download_master_data.py`
- 前提: `GOOGLE_APPLICATION_CREDENTIALS` 環境変数が設定されている

### Makefile

GCS 関連のターゲットには、開発専用であることを明記：

```makefile
# 開発専用: ローカル環境でマスターデータをダウンロード
# 本番・Stagingでは使用しないこと
data-sync-local-dev:
    python scripts/download_master_data.py
```

---

## マイグレーション手順

### 既存コードの置き換え

1. **ローカルファイル直接参照の削除**
   - `open()`, `Path("/app/...")`, `os.path.join()` などを削除
   - `FileStoragePort` 経由のアクセスに置き換え

2. **UseCase の修正**
   - コンストラクタで `FileStoragePort` を受け取る
   - ファイルアクセスは全て `storage.read_bytes()` 等を使用

3. **Router の修正**
   - `Depends(get_file_storage)` で注入
   - UseCase に渡す

4. **環境変数の設定**
   - 開発環境: `FILE_STORAGE_MODE=local`
   - 本番・Staging: `FILE_STORAGE_MODE=gcs` + 必要な環境変数

---

## 守るべきルール

1. **依存関係の方向**
   - backend_shared → 各コンテナの依存は禁止
   - 常に 各コンテナ → backend_shared の一方向依存

2. **backend_shared の責務**
   - インフラ・ポート・ユーティリティのみ
   - ドメイン・UseCase は置かない

3. **フロントエンドからのアクセス**
   - GCP / DB 直接アクセスは一切禁止
   - 必ず core_api 経由

4. **バックエンドコンテナ間通信**
   - HTTP 経由の呼び出しは極力行わない
   - 必要な場合も設計を検討したうえで例外的に扱う

5. **ローカルパスのハードコード禁止**
   - 新規コードでは必ず FileStoragePort 経由

---

## トラブルシューティング

### ImportError: google-cloud-storage

**問題:** `GcsFileStorageRepository` 初期化時にエラー

**解決策:**
```bash
pip install google-cloud-storage
```

または、`backend_shared/pyproject.toml` に依存関係が追加されているため：
```bash
pip install -e app/backend/backend_shared
```

### FileNotFoundError

**問題:** ファイルが見つからない

**確認事項:**
1. 環境変数 `FILE_STORAGE_MODE` が正しく設定されているか
2. GCS モードの場合、バケット名とプレフィックスが正しいか
3. ローカルモードの場合、ベースディレクトリが存在するか
4. パスが相対パスで指定されているか（先頭の `/` は自動で除去される）

### Permission Denied (GCS)

**問題:** GCS へのアクセスが拒否される

**確認事項:**
1. サービスアカウントに必要な権限があるか
   - `storage.objects.get`
   - `storage.objects.list`
   - (書き込みが必要な場合) `storage.objects.create`
2. `GOOGLE_APPLICATION_CREDENTIALS` が正しく設定されているか
3. 認証ファイルが存在し、読み取り可能か

---

## 今後の拡張

### BigQuery 統合

同様のパターンで BigQuery アクセスも backend_shared に集約可能：

```python
# backend_shared/core/ports/bigquery_port.py
class BigQueryPort(Protocol):
    def query(self, sql: str) -> pd.DataFrame: ...

# backend_shared/infra/gcp/bigquery_client.py
class BigQueryClient:
    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        ...
```

### 他のクラウドストレージ

AWS S3 や Azure Blob Storage にも対応可能：

```python
# backend_shared/infra/storage/s3_file_storage_repository.py
class S3FileStorageRepository:
    def __init__(self, bucket_name: str, base_prefix: str = "", ...):
        ...
```

---

## 参考資料

- **backend_shared README**: `app/backend/backend_shared/README.md`
- **core_api Clean Architecture**: `app/backend/core_api/docs/README.md`
- **FileStoragePort ソースコード**: `app/backend/backend_shared/src/backend_shared/core/ports/file_storage_port.py`

---

## 変更履歴

- **2025-11-28**: 初版作成 - GCP 共有機能の backend_shared への集約完了
