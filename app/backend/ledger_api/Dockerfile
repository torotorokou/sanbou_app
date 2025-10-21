# =========================
# ledger_api (LibreOffice 直呼び版)
# context: app/backend/ledger_api (サービス直下)
# =========================

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# backend_sharedのビルド
COPY ./backend_shared /build/backend_shared
# README.mdを作成（pyproject.tomlで必要）
RUN touch /build/backend_shared/README.md || true
RUN cd /build/backend_shared && pip wheel --no-deps . -w /wheels

COPY ./ledger_api/requirements.txt /build/requirements.txt
COPY ./ledger_api/requirements-dev.txt /build/requirements-dev.txt
ARG INSTALL_DEV=false
RUN pip install --upgrade pip \
    && pip wheel --no-deps -r /build/requirements.txt -w /wheels \
    && if [ "$INSTALL_DEV" = "true" ]; then pip wheel --no-deps -r /build/requirements-dev.txt -w /wheels; fi

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/backend:/opt/backend_shared/src
WORKDIR /backend

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
COPY ./ledger_api/requirements.txt /backend/requirements.txt
COPY ./ledger_api/requirements-dev.txt /backend/requirements-dev.txt
ARG INSTALL_DEV=false
RUN pip install --no-cache-dir /wheels/*.whl \
    && if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

# アプリコード
COPY --chown=appuser:appuser ./ledger_api/app /backend/app
COPY --chown=appuser:appuser --chmod=0755 ./ledger_api/startup.sh /backend/startup.sh

# Note: backend_shared module is mounted at runtime via docker-compose volumes
# Build-time import checks are removed to avoid dependency errors

# ログ出力用ディレクトリを作成し書き込み権限を付与
RUN mkdir -p /backend/app/api/logs \
  && chown -R appuser:appuser /backend

# main_paths.yaml で参照される想定の data / logs ディレクトリを事前生成（必要なら上書き調整）
RUN mkdir -p /backend/app/api/data/input /backend/app/api/data/output \
  && mkdir -p /backend/app/api/logs \
  && chown -R appuser:appuser /backend/app/api/data /backend/app/api/logs

ENV BASE_API_DIR=/backend/app/api
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1
ENTRYPOINT ["/backend/startup.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
