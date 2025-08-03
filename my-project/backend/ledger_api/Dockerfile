FROM python:3.10-slim

# 作業ディレクトリ
WORKDIR /backend

# 依存パッケージファイルをコピー
COPY requirements.txt .
COPY requirements-dev.txt .

# === 開発環境かどうかを判定するビルド引数（デフォルトはfalse） ===
ARG INSTALL_DEV=false

# === [開発環境のみ] システムパッケージ（例: lsof）をインストール ===
RUN apt-get update \
    && if [ "$INSTALL_DEV" = "true" ]; then apt-get install -y --no-install-recommends lsof; fi \
    && rm -rf /var/lib/apt/lists/*

# === Pythonパッケージのインストール ===
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

# アプリケーションコードをコピー
COPY ./app /backend/app

ENV PYTHONPATH=/backend

# FastAPIアプリ起動（ホットリロード付き）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
