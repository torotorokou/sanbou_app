---

## 各ディレクトリの役割

### ai_api/
- AI活用系API（OpenAI, Gemini, LangChain等での質問応答やPDF・CSV解析）
- `app/`：FastAPI本体・エンドポイント実装
- `backend_shared/`：AI系API間で共有するモジュール
- `config/`：AI用の設定ファイル
- `.env.ai_api`：AI API専用の環境変数
- `Dockerfile`：ai_api サービス用Docker定義
- `requirements.txt`：Python依存パッケージリスト

### ledger_api/
- 帳簿（帳票生成・会計処理）系API
- 各種帳簿生成、SQL保存処理、Excel/PDF出力等の機能を実装

### sql_api/
- SQLデータベース操作・DB管理用API
- テーブル作成・データ取得・スキーマ管理など

### backend_shared/
- backend内の複数APIで共通利用するモジュール・処理・ユーティリティ
- 例：認証、ロギング、共通モデル等

### shared/
- プロジェクト横断の共通ライブラリ・定数・ユーティリティ等
- frontend・backend両方で必要になる場合はこちらに実装

---

## 環境構築・起動

1. **Docker推奨**  
   各APIはDocker Composeで一括起動できます（プロジェクトルートの`docker-compose.yml`参照）。

2. **個別起動例**（ai_apiの場合）
   ```sh
   cd backend/ai_api
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

---

**このまま `backend/README.md` にご利用ください。**  
さらに、`ai_api/`や`ledger_api/`など個別APIごとにも簡単なREADMEを置くと理想的です。
