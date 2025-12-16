# =========================
# inbound_forecast_worker Dockerfile (multi-stage: wheelbuilder/base/dev/stg/prod)
# Context: app/backend
# 
# Target stages:
#   - wheelbuilder: Python 依存パッケージをビルド (wheel 生成)
#   - base: 共通ランタイムベース (wheelインストール + アプリコード配置)
#   - dev: ローカル開発用 (ホットリロード有効、editable install)
#   - stg: ステージング環境用 (base継承、AUTH_MODE=vpn_dummy 等の環境変数)
#   - prod: 本番環境用 (base継承、AUTH_MODE=iap 等の環境変数)
# =========================

# ──────────────────────────────────────────────────────────────
# Stage: wheelbuilder
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS wheelbuilder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Security: Update OS packages + scientific stack deps
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc g++ \
      libgomp1 \
      ca-certificates \
      curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Build backend_shared wheel
COPY ./backend_shared /build/backend_shared
RUN python -m pip install --upgrade "pip>=25.3,<26.0" setuptools wheel && \
    cd /build/backend_shared && \
    pip wheel --no-deps . -w /wheels

# Build app dependencies
COPY ./inbound_forecast_worker/requirements.txt /build/requirements.txt
RUN pip wheel -r /build/requirements.txt -w /wheels

# ──────────────────────────────────────────────────────────────
# Stage: dev (ホットリロード対応)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS dev
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend:/opt/backend_shared/src

WORKDIR /backend

# Install runtime deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libgomp1 \
      ca-certificates \
      curl \
      tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install wheels
COPY --from=wheelbuilder /wheels /wheels
RUN pip install --upgrade pip && \
    pip install /wheels/*.whl && \
    rm -rf /wheels

# Install backend_shared in editable mode (dev only)
COPY ./backend_shared /opt/backend_shared
RUN cd /opt/backend_shared && \
    pip install -e .

# Copy prediction scripts (for Phase 3)
COPY ./inbound_forecast_worker/scripts /backend/scripts
COPY ./inbound_forecast_worker/models /backend/models

# App code will be mounted via volume in docker-compose.dev.yml
# But copy as fallback
COPY ./inbound_forecast_worker/app /backend/app

EXPOSE 8000

CMD ["python", "-m", "app.main"]

# ──────────────────────────────────────────────────────────────
# Stage: base (stg/prod 共通ベース)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend:/opt/backend_shared/src \
    TZ=Asia/Tokyo

WORKDIR /backend

# Runtime deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libgomp1 \
      ca-certificates \
      curl \
      tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install wheels
COPY --from=wheelbuilder /wheels /wheels
RUN pip install --upgrade pip && \
    pip install /wheels/*.whl && \
    rm -rf /wheels

# Copy backend_shared
COPY ./backend_shared /opt/backend_shared

# Copy prediction scripts & models
COPY ./inbound_forecast_worker/scripts /backend/scripts
COPY ./inbound_forecast_worker/models /backend/models

# Copy app code
COPY ./inbound_forecast_worker/app /backend/app

# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1001 appuser && \
    chown -R appuser:appuser /backend

USER appuser

CMD ["python", "-m", "app.main"]

# ──────────────────────────────────────────────────────────────
# Stage: stg
# ──────────────────────────────────────────────────────────────
FROM base AS stg
ENV ENVIRONMENT=stg

# ──────────────────────────────────────────────────────────────
# Stage: prod
# ──────────────────────────────────────────────────────────────
FROM base AS prod
ENV ENVIRONMENT=prod
