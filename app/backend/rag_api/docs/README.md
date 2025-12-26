# RAG API Documentation

RAG API（Retrieval-Augmented Generation - 検索拡張生成）のドキュメント

## 概要

RAG APIは、ドキュメント検索とAI生成を組み合わせた高度な質問応答システムを提供します。
PDFマニュアルの取り込み、ベクトル検索、GPTによる回答生成を実行します。

## ディレクトリ構成

```
docs/
├── README.md          # このファイル
├── architecture/      # アーキテクチャ設計（今後追加）
├── api/              # API仕様書（今後追加）
└── guides/           # 利用ガイド（今後追加）
```

## 主な機能

- **PDF取り込み**: PDFドキュメントの読み込み・解析
- **チャンク分割**: ドキュメントの最適な分割
- **ベクトル検索**: セマンティック検索
- **GPT回答生成**: コンテキストを考慮した回答生成
- **マニュアル管理**: マニュアルのメタデータ管理

## 技術スタック

- **言語**: Python
- **フレームワーク**: FastAPI
- **AI**: OpenAI GPT API
- **PDF処理**: PyPDF2 / pdfplumber
- **ベクトルDB**: (TODO: 仕様追加)
- **コンテナ**: Docker

## アーキテクチャ

### 主要コンポーネント

```
app/
├── main.py                    # FastAPIアプリケーション
├── dependencies.py            # 依存性注入
├── api/
│   └── endpoints/
│       ├── query.py          # 質問応答エンドポイント
│       └── manuals/          # マニュアル管理
├── core/
│   ├── file_ingest_service.py   # ファイル取り込み
│   └── rag_service.py           # RAGコアロジック
├── infrastructure/
│   ├── manuals_repository.py    # マニュアルリポジトリ
│   ├── llm/
│   │   ├── ai_loader.py        # AIモデルローダー
│   │   └── openai_client.py    # OpenAIクライアント
│   └── pdf/
│       └── pdf_loader.py       # PDF読み込み
├── schemas/
│   ├── query_schema.py         # クエリスキーマ
│   └── manuals.py              # マニュアルスキーマ
└── services/
    ├── ai_response_service.py  # AI応答サービス
    ├── pdf_service.py          # PDF処理サービス
    └── manuals_service.py      # マニュアルサービス
```

## API仕様

### フロントエンド連携

詳細は [FRONTEND_API_GUIDE.md](../FRONTEND_API_GUIDE.md) を参照

### 主要エンドポイント

TODO: エンドポイント一覧を追加

## 開発ガイド

### ローカル開発

```bash
cd app/backend/rag_api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8007
```

### 環境変数

主要な環境変数:

- `OPENAI_API_KEY` - OpenAI API キー
- `OPENAI_MODEL` - 使用するGPTモデル
- `VECTOR_DB_PATH` - ベクトルDB保存先
- `PDF_DATA_PATH` - PDFデータディレクトリ

## データフロー

1. **PDFアップロード**: ユーザーがPDFをアップロード
2. **テキスト抽出**: PDFからテキストを抽出
3. **チャンク分割**: 適切なサイズに分割
4. **ベクトル化**: テキストを埋め込みベクトルに変換
5. **保存**: ベクトルDBに保存
6. **検索**: ユーザークエリに対して類似検索
7. **生成**: GPTで回答を生成

## ユーティリティ

### チャンク処理

- `chunk_utils.py`: チャンク分割ユーティリティ

### ファイル処理

- `file_utils.py`: ファイル操作
- `utils.py`: 汎用ユーティリティ

## テスト

```bash
cd app/backend/rag_api
pytest tests/
```

## 関連ドキュメント

- Manual API: マニュアルメタデータ連携
- AI API: 基本的なAI機能
- [FRONTEND_API_GUIDE.md](../FRONTEND_API_GUIDE.md)
- プロジェクト全体: `/docs/`

## 今後の予定

- [ ] ベクトルDB仕様の詳細化
- [ ] API仕様書の完成
- [ ] パフォーマンス最適化ガイド
- [ ] チャンク戦略の詳細ドキュメント
- [ ] ユーザーガイドの作成
