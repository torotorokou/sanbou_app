# AI API Documentation

AI API（OpenAI GPT連携・AI機能）のドキュメント

## 概要

AI APIは、OpenAI GPTとの連携を提供し、自然言語処理やAI機能を実装するためのサービスです。

## ディレクトリ構成

```
docs/
├── README.md          # このファイル
├── architecture/      # アーキテクチャ設計（今後追加）
├── api/              # API仕様・エンドポイント定義（今後追加）
└── implementation/    # 実装ガイド（今後追加）
```

## 主な機能

- OpenAI GPT APIとの連携
- プロンプト管理
- レスポンス処理
- エラーハンドリング

## 技術スタック

- **言語**: Python
- **フレームワーク**: FastAPI
- **AI**: OpenAI GPT API
- **コンテナ**: Docker

## 開発ガイド

### ローカル開発

```bash
cd app/backend/ai_api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 環境変数

主要な環境変数:

- `OPENAI_API_KEY` - OpenAI API キー
- `OPENAI_MODEL` - 使用するモデル名

## API仕様

TODO: API仕様を追加

## 関連ドキュメント

- [OpenAI API Documentation](https://platform.openai.com/docs)
- プロジェクト全体のドキュメント: `/docs/`

## 今後の予定

- [ ] API仕様書の作成
- [ ] アーキテクチャ設計書の追加
- [ ] 実装ガイドの作成
- [ ] ユースケース別サンプルの追加
