FROM python:3.10

WORKDIR /backend

# 依存パッケージファイルをコピー（サービス配下）
COPY sql_api/requirements.txt ./requirements.txt
COPY sql_api/requirements-dev.txt ./requirements-dev.txt

# === 開発環境かどうかを判定するビルド引数（デフォルトはfalse） ===
ARG INSTALL_DEV=false

# === [開発環境のみ] システムパッケージ（例: lsof）をインストール ===
RUN apt-get update \
    && if [ "$INSTALL_DEV" = "true" ]; then apt-get install -y lsof; fi \
    && rm -rf /var/lib/apt/lists/*

# === Pythonパッケージのインストール ===
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

# 共有モジュールを同梱
COPY backend_shared/ /backend/backend_shared

# アプリ本体と設定をコピー（サービス配下）
COPY sql_api/app /backend/app
COPY sql_api/config /backend/config

ENV PYTHONPATH=/backend

# サーバ起動コマンド（開発・本番共通）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
