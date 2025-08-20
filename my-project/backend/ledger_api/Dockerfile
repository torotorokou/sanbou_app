FROM debian:bookworm-slim

WORKDIR /backend

# パッケージリストファイルをコピー（サービス配下）
COPY ledger_api/apt-packages.txt ./apt-packages.txt

# 必須パッケージ・日本語フォントを一括インストール
RUN apt-get update \
    && grep -vE '^\s*#' apt-packages.txt | xargs apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Python 依存関係（サービス配下）
COPY ledger_api/requirements.txt ./requirements.txt
COPY ledger_api/requirements-dev.txt ./requirements-dev.txt

# 開発環境判定用ビルド引数（デフォルトfalse）
ARG INSTALL_DEV=false

# pip install時、PEP668突破用オプション付き
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt \
    && if [ "$INSTALL_DEV" = "true" ]; then pip3 install --no-cache-dir --break-system-packages -r requirements-dev.txt; fi

# 共有モジュールを同梱
COPY backend_shared/ /backend/backend_shared

# アプリケーションコードと設定をコピー（サービス配下）
COPY ledger_api/app /backend/app
COPY ledger_api/config /backend/config

# PYTHONPATHを設定
ENV PYTHONPATH=/backend

# uno動作確認・unoconv動作確認（ビルド時のエラー早期検知用）
RUN python3 -c "import uno"
RUN unoconv --version

# FastAPIアプリ起動（ホットリロード付き）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
