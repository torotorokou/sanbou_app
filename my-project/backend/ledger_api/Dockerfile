## syntax=docker/dockerfile:1.6
# =========================
# ledger_api (LibreOffice 直呼び版)
# - unoconv / python3-uno は不要
# - LibreOffice と日本語フォントのみインストール
# =========================

# ---- builder: wheel化で高速再ビルド ----
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build
ARG SERVICE_DIR=ledger_api

# サービス個別の requirements をルート build context からコピー
COPY ${SERVICE_DIR}/requirements.txt requirements.txt
COPY ${SERVICE_DIR}/requirements-dev.txt requirements-dev.txt
ARG INSTALL_DEV=false
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-deps -r requirements.txt -w /wheels \
    && if [ "$INSTALL_DEV" = "true" ]; then \
         pip wheel --no-deps -r requirements-dev.txt -w /wheels; \
       fi

# ---- runtime ----
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/backend
WORKDIR /backend
ARG SERVICE_DIR=ledger_api

# LibreOffice と日本語フォント、ヘルスチェック用 curl
RUN apt-get update && apt-get install -y --no-install-recommends \
      libreoffice \
      fonts-noto-cjk fonts-noto-cjk-extra \
      fonts-ipafont-mincho fonts-ipafont-gothic \
      curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 念のため libreoffice の実体パスを PATH に追加（多くの環境では不要）
ENV PATH="/usr/lib/libreoffice/program:${PATH}"

# 非rootユーザー
RUN useradd -m appuser

# Python 依存関係
COPY --from=builder /wheels /wheels
COPY ${SERVICE_DIR}/requirements.txt requirements.txt
COPY ${SERVICE_DIR}/requirements-dev.txt requirements-dev.txt
ARG INSTALL_DEV=false
RUN pip install --no-cache-dir /wheels/*.whl \
    && if [ "$INSTALL_DEV" = "true" ]; then \
         pip install --no-cache-dir -r requirements-dev.txt; \
       fi

# アプリ本体と共有コード
COPY backend_shared/ /backend/backend_shared
COPY ${SERVICE_DIR}/app /backend/app
# ログ出力用ディレクトリを作成し書き込み権限を付与
RUN mkdir -p /backend/app/api/st_app/logs \
  && chown -R appuser:appuser /backend

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
