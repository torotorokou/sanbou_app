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
ARG BASE_PATH=backend

# サービス個別の requirements をルート build context からコピー
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt requirements.txt
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements-dev.txt requirements-dev.txt
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
ARG BASE_PATH=backend

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
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt requirements.txt
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements-dev.txt requirements-dev.txt
ARG INSTALL_DEV=false
RUN pip install --no-cache-dir /wheels/*.whl \
    && if [ "$INSTALL_DEV" = "true" ]; then \
         pip install --no-cache-dir -r requirements-dev.txt; \
       fi

# アプリ本体と共有コード
COPY ${BASE_PATH}/backend_shared/ /backend/backend_shared
COPY ${BASE_PATH}/${SERVICE_DIR}/app /backend/app
# --- マスタCSV / テンプレート類を含める (dev は volume で存在、stg/prod はイメージに同梱が必要) ---
COPY ${BASE_PATH}/${SERVICE_DIR}/app/st_app/data/master /backend/app/st_app/data/master
COPY ${BASE_PATH}/${SERVICE_DIR}/app/st_app/data/templates /backend/app/st_app/data/templates
COPY config /backend/config
# --- build-time sanity checks (fail fast if sources missing) ---
RUN test -d /backend/app/api/endpoints/reports \
 && python - <<'PY'
import importlib, sys
sys.path.insert(0, '/backend')
importlib.import_module('app.api.endpoints.reports')
print('Verified import: app.api.endpoints.reports')
PY
# ログ出力用ディレクトリを作成し書き込み権限を付与
RUN mkdir -p /backend/app/st_app/logs \
  && chown -R appuser:appuser /backend

# main_paths.yaml で参照される想定の data / logs ディレクトリを事前生成（必要なら上書き調整）
RUN mkdir -p /backend/app/st_app/data/input /backend/app/st_app/data/output \
  && mkdir -p /backend/app/st_app/logs \
  && chown -R appuser:appuser /backend/app/st_app/data /backend/app/st_app/logs

ENV BASE_ST_APP_DIR=/backend/app/st_app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
