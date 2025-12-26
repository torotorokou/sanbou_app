# マニュアルアセット GCP 移行計画

**作成日**: 2025-12-26  
**目的**: ローカル配信からGCS（Google Cloud Storage）への移行ガイド

---

## 1. 現在のアーキテクチャ

### アセット配置

```
manual_api/
├── data/                          # 旧アセット（互換性維持）
│   └── master/vender/
│       ├── vender_fllowchart.png
│       └── vender_movie.mp4
└── local_data/                    # 新マニュアル動画アセット
    └── manuals/
        ├── index.json             # メタデータ（DB代替）
        ├── thumbs/                # サムネイル画像
        │   ├── master__01__vendor.png
        │   └── ...
        └── videos/                # 動画ファイル（.gitignore対象）
            └── ...
```

### URL パス設計

| 用途 | ローカル配信URL | BFF経由URL |
|------|-----------------|------------|
| 旧アセット | `http://manual_api:8000/manual/assets/{path}` | `/core_api/manual/assets/{path}` |
| 新アセット | `http://manual_api:8000/manual-assets/{path}` | `/core_api/manual/manual-assets/{path}` |

### コード構成

```
manual_api/app/
├── main.py                        # StaticFiles マウント
├── infra/adapters/
│   ├── catalog_data.py            # URL生成ヘルパー
│   ├── manuals_repository.py      # カタログ取得
│   └── local_video_repository.py  # index.json 読み込み
└── utils/
    └── utils.py                   # build_manual_asset_url()

core_api/app/api/routers/manual/
└── router.py                      # BFF プロキシ
```

---

## 2. GCS 移行時の変更ポイント

### 2.1 GCS バケット設計

```
gs://sanbouapp-{env}/
└── manual_assets/
    ├── index.json           # メタデータ
    ├── thumbs/
    │   ├── master__01__vendor.png
    │   └── ...
    └── videos/
        ├── master__01__vendor.mp4
        └── ...
```

### 2.2 変更が必要なファイル

#### (A) manual_api/app/main.py

```diff
- # 新マニュアル動画アセット（local_data/manuals/）
- manual_assets_dir = Path(__file__).resolve().parent.parent / "local_data" / "manuals"
- if manual_assets_dir.exists():
-     app.mount(
-         "/manual-assets",
-         StaticFiles(directory=manual_assets_dir),
-         name="manual-video-assets",
-     )

+ # GCS移行後は StaticFiles マウントを削除
+ # URL生成は署名付きURLに切り替え
```

#### (B) manual_api/app/infra/adapters/catalog_data.py

```diff
- def _get_video_asset_base_url() -> str:
-     env_url = os.getenv("MANUAL_VIDEO_ASSET_BASE_URL", "").strip()
-     if env_url:
-         return env_url.rstrip("/")
-     return "/core_api/manual/manual-assets"

+ def _get_video_asset_base_url() -> str:
+     """GCS 署名付き URL を生成するプロバイダに切り替え"""
+     return ""  # 署名付きURLは個別に生成

+ def build_manual_video_asset_url(relative_path: str) -> str:
+     """GCS署名付きURLを生成"""
+     from app.infra.gcs.signed_url import generate_signed_url
+     bucket = os.getenv("MANUAL_ASSETS_GCS_BUCKET", "sanbouapp-dev")
+     blob_path = f"manual_assets/{relative_path}"
+     return generate_signed_url(bucket, blob_path, expiration_minutes=60)
```

#### (C) 新規: manual_api/app/infra/gcs/signed_url.py

```python
"""GCS 署名付きURL生成"""
from datetime import timedelta
from google.cloud import storage

def generate_signed_url(
    bucket_name: str,
    blob_path: str,
    expiration_minutes: int = 60,
) -> str:
    """V4署名付きURLを生成"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="GET",
    )
    return url
```

#### (D) core_api/app/api/routers/manual/router.py

```diff
  @router.get("/manual-assets/{file_path:path}")
  async def proxy_manual_video_assets(file_path: str, request: Request):
-     """マニュアル動画アセット取得（ローカルプロキシ）"""
-     upstream = f"{MANUAL_API_BASE}/manual-assets/{file_path}"
-     # ... プロキシ処理 ...

+     """マニュアル動画アセット取得
+     
+     GCS移行後のオプション:
+     1. 署名付きURLへリダイレクト（推奨）
+     2. manual_api から署名付きURLを取得してレスポンス
+     """
+     # オプション1: 署名付きURLへリダイレクト
+     signed_url = await get_signed_url_from_manual_api(file_path)
+     return RedirectResponse(url=signed_url, status_code=302)
```

### 2.3 フロントエンド

**変更不要**

フロントエンドはAPIから返されるURLをそのまま使用するため、バックエンドの変更のみで完結します。

```typescript
// ItemCard.tsx - 変更不要
<img src={item.thumbnailUrl} alt={item.title} />

// VideoPane.tsx - 変更不要  
<video src={src} controls />
```

---

## 3. 移行ステップ

### Phase 1: GCS バケット準備

```bash
# バケット作成
gsutil mb -l asia-northeast1 gs://sanbouapp-${ENV}

# ディレクトリ構造作成
gsutil cp local_data/manuals/index.json gs://sanbouapp-${ENV}/manual_assets/
gsutil -m cp -r local_data/manuals/thumbs gs://sanbouapp-${ENV}/manual_assets/
gsutil -m cp -r local_data/manuals/videos gs://sanbouapp-${ENV}/manual_assets/
```

### Phase 2: index.json をGCSから読み込み

1. `local_video_repository.py` を `gcs_video_repository.py` に差し替え
2. DI設定で `LocalManualVideoRepository` → `GcsManualVideoRepository` に切り替え

### Phase 3: 署名付きURL生成に移行

1. `catalog_data.py` の `build_manual_video_asset_url()` を署名付きURL生成に変更
2. `main.py` から `StaticFiles` マウントを削除
3. `core_api` のプロキシをリダイレクト方式に変更

### Phase 4: CDN 設定（オプション）

```
Cloud CDN → Cloud Load Balancing → GCS バケット
```

- サムネイル: 長期キャッシュ（24時間以上）
- 動画: 短期キャッシュ（1時間）+ Range リクエスト対応

---

## 4. 環境変数

### 現在（ローカル配信）

```bash
# 未設定の場合は /core_api/manual/manual-assets を使用
MANUAL_VIDEO_ASSET_BASE_URL=
```

### GCS移行後

```bash
# GCS バケット名
MANUAL_ASSETS_GCS_BUCKET=sanbouapp-prod

# サービスアカウント（署名付きURL生成用）
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## 5. キャッシュ戦略

| リソース | ローカル | GCS + CDN |
|----------|----------|-----------|
| index.json | なし | 5分 |
| thumbs/*.png | 1日（BFF設定） | 24時間（CDN） |
| videos/*.mp4 | 1時間（BFF設定） | 1時間（CDN） |

### Cache-Control ヘッダー

```python
# サムネイル
blob.cache_control = "public, max-age=86400"

# 動画
blob.cache_control = "public, max-age=3600"
```

---

## 6. ロールバック手順

GCS移行後に問題が発生した場合:

1. 環境変数 `MANUAL_VIDEO_ASSET_BASE_URL` をローカルパスに戻す
2. `main.py` の `StaticFiles` マウントを再有効化
3. デプロイ

---

## 7. 差し替えポイント一覧

| 現在の実装 | GCS移行後 | ファイル |
|------------|-----------|----------|
| `StaticFiles` マウント | 削除 | `main.py` |
| `build_manual_video_asset_url()` | 署名付きURL生成 | `catalog_data.py` |
| `LocalManualVideoRepository` | `GcsManualVideoRepository` | `di_providers.py` |
| BFFプロキシ | リダイレクト | `core_api/.../router.py` |

---

## 8. セキュリティ考慮事項

### 署名付きURL

- 有効期限: 60分（調整可能）
- IPアドレス制限: オプション
- HTTPSのみ

### IAM設定

```yaml
# manual_api サービスアカウント
roles:
  - storage.objectViewer  # オブジェクト読み取り
  - storage.objectAdmin   # 署名付きURL生成（V4署名）
```

---

## まとめ

現在の実装は以下の設計原則に従っており、GCS移行が容易です:

1. **URL生成の一元化**: `build_manual_video_asset_url()` を変更するだけ
2. **リポジトリパターン**: `LocalManualVideoRepository` → `GcsManualVideoRepository` の差し替え
3. **BFFプロキシ**: リダイレクト方式への変更でフロント変更不要
4. **フロント変更不要**: APIが返すURLをそのまま使用

移行作業は1-2時間程度で完了できる見込みです。
