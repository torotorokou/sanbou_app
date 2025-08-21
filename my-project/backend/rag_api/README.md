# RAG API（rag_api）

## 概要
RAG APIは、産業廃棄物処理に関する構造化データ・AI・ベクトル検索を組み合わせて、ユーザーの質問に高精度な回答を返すAPIサービスです。

- FastAPI + LangChain + OpenAI + GCS連携
- GCSから構造化データを自動取得
- OpenAI API/Google Cloud認証対応
- Dockerコンテナで簡単デプロイ

---

## 1. 必要ファイル・ディレクトリ構成

```
rag_api/
├── app/
│   ├── ...（API/AI/ユーティリティ各種Pythonファイル）
├── requirements.txt
├── Dockerfile
├── startup.sh
├── README.md  ← このファイル
└── ...
```

-- GCSサービスアカウントキー: `secrets/gcs-key.json`
- OpenAI APIキー: `.env` または `envs/.env.rag_api` に `OPENAI_API_KEY=...`

---

## 2. 環境変数例（envs/.env.rag_api）

```
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json
```

---

## 3. 起動方法

### Docker Compose（推奨）

```bash
docker compose build rag_api
# またはキャッシュ無効化
docker compose build --no-cache rag_api

docker compose up rag_api
```

### 単体Docker

```bash
docker build -t rag_api .
docker run --env-file ../envs/.env.rag_api -v $(pwd)/secrets/gcs-key.json:/root/.config/gcloud/application_default_credentials.json rag_api
```

---

## 4. API仕様

- OpenAPI/Swagger UI: [http://localhost:8004/rag_api/docs](http://localhost:8004/rag_api/docs)
- 主要エンドポイント: `/api/generate-answer`（POST）

### リクエスト例
```json
{
  "query": "比重差選別機ALCHEMIの選別精度は？",
  "category": "設備",
  "tags": ["ALCHEMI", "ターンソーター"]
}
```

### レスポンス例
```json
{
  "answer": "...AIによる回答...",
  "sources": ["..."],
  "pages": ["..."]
}
```

---

## 5. よくあるトラブル

- 改行コードはLF（Unix）推奨
- GCSキーや.envファイルのパス・権限に注意
- データが取得できない場合はGCSバケットやlocal_data配下を確認

---

## 6. 開発・拡張Tips

- 設定値は環境変数で柔軟に上書き可能
- コードはOCP（拡張に開き修正に閉じる）を意識した設計
- FastAPI/uvicornのホットリロードは`--reload`オプションで

---

## 7. ライセンス

本リポジトリは社内利用・検証目的です。商用利用時はご相談ください。
