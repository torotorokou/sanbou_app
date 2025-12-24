# メンテナンスページ用 Dockerfile
# Cloud Run 最小構成：python:3.11-slim + FastAPI + uvicorn

FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY main.py .

# Cloud Run のデフォルトポート（環境変数 PORT で上書き可能）
ENV PORT=8080

# 非rootユーザーで実行（セキュリティベストプラクティス）
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# uvicorn でアプリケーションを起動
# - host=0.0.0.0: すべてのインターフェースでリッスン
# - port=$PORT: Cloud Run が設定するポートを使用
# - workers=1: 最小構成（Cloud Run のオートスケールに依存）
# - timeout-keep-alive=5: 短いキープアライブ（コスト削減）
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 5
