# Manual API Documentation

Manual API（マニュアル管理・提供）のドキュメント

## 概要

Manual APIは、各種マニュアル・ドキュメントの管理、検索、提供を行うサービスです。

## ディレクトリ構成

```
docs/
├── README.md          # このファイル
├── architecture/      # アーキテクチャ設計（今後追加）
├── api/              # API仕様書（今後追加）
└── guides/           # 利用ガイド（今後追加）
```

## 主な機能

- マニュアルカタログ管理
- マニュアル検索
- マニュアルメタデータ提供
- ベンダー情報管理

## 技術スタック

- **言語**: Python
- **フレームワーク**: FastAPI
- **データストレージ**: ファイルシステム
- **コンテナ**: Docker

## API構成

### 主要コンポーネント

- **main.py**: FastAPIアプリケーション
- **routers.py**: ルーティング定義
- **service.py**: ビジネスロジック
- **repository.py**: データアクセス層
- **schemas.py**: データスキーマ定義
- **catalog_data.py**: カタログデータ管理

## データ構造

### マスターデータ

- ベンダー情報: `data/master/vender/`

## 開発ガイド

### ローカル開発

```bash
cd app/backend/manual_api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8006
```

### 環境変数

主要な環境変数:

- `MANUAL_DATA_PATH` - マニュアルデータディレクトリ
- `PORT` - APIポート番号（デフォルト: 8006）

## API エンドポイント

TODO: エンドポイント一覧を追加

## 関連ドキュメント

- RAG API: マニュアル検索機能と連携
- プロジェクト全体: `/docs/`

## 今後の予定

- [ ] API仕様書の作成
- [ ] マニュアル管理ガイドの追加
- [ ] 検索機能の詳細ドキュメント
- [ ] データモデル図の作成
