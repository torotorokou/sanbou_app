# Manual API 現状把握レポート

**作成日**: 2025-12-26  
**目的**: マニュアル動画＋サムネイルのローカル配信機能を追加するための現状分析

---

## 1. ディレクトリ構造

```
app/backend/manual_api/
├── Dockerfile
├── requirements.txt
├── startup.sh                    # uvicorn 起動スクリプト
├── app/
│   ├── main.py                   # FastAPI アプリ初期化
│   ├── api/
│   │   └── routers/
│   │       └── manuals.py        # /manual/manuals/* ルータ
│   ├── config/
│   │   ├── __init__.py
│   │   ├── di_providers.py       # DI 設定（リポジトリ/サービス）
│   │   └── settings.py           # 環境変数設定
│   ├── core/
│   │   ├── domain/
│   │   │   └── manual_entity.py  # エンティティ/レスポンス型
│   │   ├── ports/
│   │   │   └── manuals_repository.py  # リポジトリ抽象
│   │   └── usecases/
│   │       └── manuals_service.py     # ユースケース
│   ├── infra/
│   │   └── adapters/
│   │       ├── catalog_data.py        # ハードコードされたカタログデータ
│   │       └── manuals_repository.py  # InMemoryManualRepository
│   └── utils/
│       └── utils.py               # アセットURL生成ヘルパー
└── data/
    └── master/
        └── vender/
            ├── vender_fllowchart.png  # 既存サムネイル
            └── vender_movie.mp4       # 既存動画
```

---

## 2. 起動方法

### ローカル開発環境（Docker Compose）

```bash
# プロジェクトルートから
make up ENV=local_dev

# または直接
docker compose -f docker/docker-compose.dev.yml -p local_dev up -d manual_api
```

### manual_api 単体起動

```bash
# コンテナ内
bash startup.sh
# → uvicorn app.main:app --host 0.0.0.0 --port 8000 ${DEV_RELOAD:+--reload}
```

### ポート

- **manual_api**: `8005:8000` (`DEV_MANUAL_API_PORT`)
- **core_api (BFF)**: `8003:8000` (`DEV_CORE_API_PORT`)
- **frontend**: `5173:5173`

---

## 3. 現状のエンドポイント一覧

### manual_api 直接（内部用）

| Method | Path | 概要 |
|--------|------|------|
| GET | `/health`, `/__health` | ヘルスチェック |
| GET | `/manual/manuals` | マニュアル一覧取得 |
| GET | `/manual/manuals/catalog` | カタログ取得（セクション別） |
| GET | `/manual/manuals/{manual_id}` | マニュアル詳細 |
| GET | `/manual/manuals/{manual_id}/sections` | セクション取得 |
| (mount) | `/manual/assets/*` | 静的ファイル配信（`data/` ディレクトリ） |

### core_api (BFF) 経由（フロントエンド用）

| Method | Path | Upstream |
|--------|------|----------|
| GET | `/core_api/manual/manuals` | → `manual_api:/manual/manuals` |
| GET | `/core_api/manual/manuals/catalog` | → `manual_api:/manual/manuals/catalog` |
| GET | `/core_api/manual/manuals/{id}` | → `manual_api:/manual/manuals/{id}` |
| GET | `/core_api/manual/manuals/{id}/sections` | → `manual_api:/manual/manuals/{id}/sections` |
| GET | `/core_api/manual/assets/{path}` | → `manual_api:/manual/assets/{path}` |
| POST | `/core_api/manual/search` | → `manual_api:/manual/search` |
| GET | `/core_api/manual/toc` | → `manual_api:/manual/toc` |
| GET | `/core_api/manual/categories` | → `manual_api:/manual/categories` |
| GET | `/core_api/manual/docs/{doc_id}/{filename}` | → `manual_api:/manual/docs/{doc_id}/{filename}` |

---

## 4. 静的配信の現状

### 現在の実装 (main.py)

```python
data_dir = Path(__file__).resolve().parent.parent / "data"
if data_dir.exists():
    app.mount("/manual/assets", StaticFiles(directory=data_dir), name="manual-assets")
```

- **マウントパス**: `/manual/assets`
- **対象ディレクトリ**: `manual_api/data/`
- **BFF経由のURL**: `/core_api/manual/assets/{path}`
- **フロントエンド用URL**: 環境変数 `MANUAL_ASSET_BASE_URL` または `/core_api/manual/assets`

### 既存のファイル

```
data/master/vender/
  ├── vender_fllowchart.png
  └── vender_movie.mp4
```

### URL生成ヘルパー (utils.py)

```python
def build_manual_asset_url(relative_path: str) -> str:
    """
    - MANUAL_ASSET_BASE_URL が設定されていれば使用
    - 未設定なら /core_api/manual/assets を使用
    - 将来GCS署名付きURLに差し替え可能
    """
```

---

## 5. カタログデータの現状

### catalog_data.py

- **ハードコードされた Python dict** として定義
- セクション（master, contract, estimate, manifest, external-input）
- 各アイテムに `thumbnail_url`, `video_url`, `flow_url` を持つ
- 多くは `https://via.placeholder.com` を使用（ダミー）
- 一部（vendor）は `build_manual_asset_url()` でローカルアセット参照

### 課題

1. カタログデータがハードコードされており、拡張性が低い
2. サムネイル/動画の多くがダミーURL
3. DB/JSONファイル化されていない

---

## 6. 今回追加する変更点

### Step 1: ローカル資産の配置

```
manual_api/
└── local_data/
    └── manuals/
        ├── index.json           # マニュアル一覧（seed）
        ├── thumbs/
        │   ├── master__01__vendor.png
        │   └── ...
        └── videos/              # .gitignore対象
            └── ...
```

### Step 2: API/静的配信の追加

1. **静的配信マウント**: `/manual-assets` → `local_data/manuals`
2. **カタログ拡張**: `index.json` から読み込み、既存 `catalog_data.py` とマージ
3. **URL生成の統一**: `thumb_url`, `video_url` を統一形式で返す

### Step 3: フロントエンド対応

1. 既存の `features/manual` を活用
2. `ItemCard` でサムネイル表示（既に対応済み）
3. `VideoPane` で動画再生（既に対応済み）

### 差し替えポイント（GCP移行時）

| 現在 | 将来（GCS） |
|------|-------------|
| `StaticFiles` マウント | 削除 |
| `build_manual_asset_url()` | GCS署名付きURL生成に差し替え |
| `LocalManualRepository` | `GcsManualRepository` に切り替え |

---

## 7. Clean Architecture 準拠確認

### 現在の構成

```
┌─────────────────────────────────────────────────────────────┐
│ routers/manuals.py (API層)                                  │
│   └─ Depends(get_manuals_service)                           │
├─────────────────────────────────────────────────────────────┤
│ usecases/manuals_service.py (ユースケース層)                 │
│   └─ ManualsService(repo: ManualsRepository)                │
├─────────────────────────────────────────────────────────────┤
│ ports/manuals_repository.py (ポート層 - 抽象)               │
│   └─ ABC: list, get, get_sections, get_catalog             │
├─────────────────────────────────────────────────────────────┤
│ infra/adapters/manuals_repository.py (インフラ層 - 実装)    │
│   └─ InMemoryManualRepository                               │
│   └─ catalog_data.py (ハードコードデータ)                   │
└─────────────────────────────────────────────────────────────┘
```

### 今回の追加

- **ポート変更なし**: 既存の `ManualsRepository` インターフェースを維持
- **インフラ層**: `catalog_data.py` を `index.json` 読み込みに変更
- **DI維持**: `di_providers.py` から注入される構造を維持

---

## 8. セキュリティ方針

### 現在

- 開発環境: 無認証（直接アクセス可能）
- 本番環境: core_api (BFF) 経由、IAP/トークン認証

### 今回の対応

- 開発環境: 引き続き無認証
- 本番環境: 変更なし（BFF経由のまま）

---

## まとめ

manual_api は Clean Architecture (Ports & Adapters) に準拠しており、静的配信の基盤（`StaticFiles`）も既に存在します。今回は:

1. `local_data/manuals/` に新しい資産ディレクトリを追加
2. `index.json` を作成してサムネイル/動画メタデータを管理
3. 既存の `catalog_data.py` を `index.json` 読み込みに移行
4. フロントエンドは既存コンポーネントで対応可能

将来のGCP移行は、`build_manual_asset_url()` と `InMemoryManualRepository` の差し替えのみで完了できる設計です。
