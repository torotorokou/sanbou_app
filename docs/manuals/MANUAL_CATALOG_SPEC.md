# マニュアルカタログ仕様書

> **Single Source of Truth**: `local_data/manuals/index.json`

## 概要

manual_api のマニュアルカタログは `index.json` を唯一の正本として管理します。
バックエンド・フロントエンドともにこのファイルからデータを取得します。

## ディレクトリ構造

```
app/backend/manual_api/local_data/manuals/
├── index.json           # カタログ正本（27項目）
├── .gitignore           # 動画ファイル除外設定
├── thumbs/              # サムネイル画像
│   └── m11_master_vendor.png
├── videos/              # 動画ファイル（git 管理外）
│   └── m11_master_vendor.mp4
├── flowcharts/          # フローチャート画像
│   └── m11_master_vendor.png
└── contents/            # Markdown コンテンツ
    ├── m11_master_vendor.md
    ├── m12_master_unitprice.md
    └── ...
```

## index.json スキーマ

```json
{
  "version": 1,
  "manuals": [
    {
      "id": "m11_master_vendor",
      "no": 11,
      "major": "マスター作成",
      "title": "業者",
      "description": "運搬業者・処分業者マスタの管理方法...",
      "order": 11,
      "icon": "FolderOpenOutlined",
      "tags": ["業者", "マスター", "運搬", "処分"],
      "assets": {
        "thumb": "thumbs/m11_master_vendor.png",
        "video": "videos/m11_master_vendor.mp4",
        "flowchart": "flowcharts/m11_master_vendor.png"
      },
      "content_path": "contents/m11_master_vendor.md"
    }
  ]
}
```

### フィールド説明

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `id` | string | ✓ | 一意識別子（例: `m11_master_vendor`） |
| `no` | integer | ✓ | 番号（11, 12, ...）UI表示・ソート用 |
| `major` | string | ✓ | 大項目（セクション名として使用） |
| `title` | string | ✓ | 項目名 |
| `description` | string | ✓ | 説明文 |
| `order` | integer | ✓ | 表示順序 |
| `icon` | string | ✓ | Ant Design アイコン名 |
| `tags` | string[] | ✓ | 検索用タグ |
| `assets.thumb` | string? | | サムネイル画像の相対パス |
| `assets.video` | string? | | 動画ファイルの相対パス |
| `assets.flowchart` | string? | | フローチャート画像の相対パス |
| `content_path` | string | ✓ | Markdown コンテンツの相対パス |

## 大項目（major）一覧

| No範囲 | major | アイコン |
|--------|-------|----------|
| 11-15 | マスター作成 | FolderOpenOutlined |
| 21-23 | 契約書 | FileProtectOutlined |
| 31 | 見積書 | FileTextOutlined |
| 41-46 | マニフェスト | FileDoneOutlined |
| 51-53 | 工場外入力 | CloudUploadOutlined |
| 61-63 | 請求書・支払い関係 | DollarOutlined |
| 71-74 | 電子マニフェスト | FileSyncOutlined |
| 81-82 | 報告書 | FileSearchOutlined |

## API エンドポイント

### カタログ一覧
```
GET /api/v1/manuals/catalog?category=shogun
```

レスポンス:
```json
{
  "sections": [
    {
      "id": "sec-1",
      "title": "マスター作成",
      "icon": "FolderOpenOutlined",
      "items": [
        {
          "id": "m11_master_vendor",
          "title": "業者",
          "description": "...",
          "tags": ["業者", "マスター"],
          "route": "/manuals/shogun/m11_master_vendor",
          "thumbnail_url": "/core_api/manual/manual-assets/thumbs/m11_master_vendor.png",
          "video_url": "/core_api/manual/manual-assets/videos/m11_master_vendor.mp4",
          "flow_url": "/core_api/manual/manual-assets/flowcharts/m11_master_vendor.png"
        }
      ]
    }
  ]
}
```

### マニュアル詳細
```
GET /api/v1/manuals/{manual_id}
```

## アセット URL 生成

```python
# catalog_data.py
def build_manual_asset_url(relative_path: str | None) -> str | None:
    """
    環境変数 MANUAL_ASSET_BASE_URL があればそれを使用
    なければ /core_api/manual/manual-assets を使用（BFF経由）
    """
```

### 環境別設定

| 環境 | MANUAL_ASSET_BASE_URL |
|------|----------------------|
| ローカル | (未設定) → `/core_api/manual/manual-assets` |
| ステージング | `https://storage.googleapis.com/sanbou-stg/manuals` |
| 本番 | `https://storage.googleapis.com/sanbou-prod/manuals` |

## GCS 移行手順

1. **index.json の移行**
   - `load_manual_index()` を GCS から取得するよう変更
   - Cloud Storage JSON API または署名付き URL を使用

2. **アセット URL の変更**
   - 環境変数 `MANUAL_ASSET_BASE_URL` を GCS バケット URL に設定
   - 署名付き URL が必要な場合は `build_manual_asset_url()` を拡張

3. **コンテンツの移行**
   - `load_manual_content()` を GCS から取得するよう変更

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|----------|
| 2025-01-08 | 1.0 | 初版作成。27項目の新スキーマ導入 |
