FROM python:3.10

WORKDIR /backend

# 依存パッケージファイルをコピー
COPY requirements.txt .
COPY requirements-dev.txt .

# === 開発環境かどうかを判定するビルド引数（デフォルトはfalse） ===
ARG INSTALL_DEV=false

# === [開発環境のみ] システムパッケージ（例: lsof）をインストール ===
RUN apt-get update \
    # INSTALL_DEVがtrueの場合だけlsofをインストール
    && if [ "$INSTALL_DEV" = "true" ]; then apt-get install -y lsof; fi \
    # キャッシュクリア
    && rm -rf /var/lib/apt/lists/*

# === Pythonパッケージのインストール ===
RUN pip install --no-cache-dir -r requirements.txt \
    # INSTALL_DEVがtrueの場合だけdevパッケージもインストール
    && if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

# アプリ本体をコピー
COPY ./app /backend/app

ENV PYTHONPATH=/backend

# サーバ起動コマンド（開発・本番共通）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
