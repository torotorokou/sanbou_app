# =========================
# forecast_worker Dockerfile (multi-stage: dev/prod)
# Context: app/backend
# =========================

# ──────────────────────────────────────────────────────────────
# Stage: base
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      curl \
      libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# ──────────────────────────────────────────────────────────────
# Stage: wheelbuilder
# ──────────────────────────────────────────────────────────────
FROM base AS wheelbuilder
COPY ./backend_shared /build/backend_shared
RUN pip install --upgrade pip setuptools wheel && \
    cd /build/backend_shared && \
    pip wheel --no-deps . -w /wheels

COPY ./forecast_worker/requirements.txt /build/requirements.txt
RUN pip wheel --no-deps -r /build/requirements.txt -w /wheels

# ──────────────────────────────────────────────────────────────
# Stage: dev (開発環境)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS dev
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/worker:/opt/backend_shared/src

WORKDIR /worker

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      libpq5 && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m workeruser

COPY ./forecast_worker/requirements.txt /worker/requirements.txt
RUN pip install --no-cache-dir -r /worker/requirements.txt

# backend_shared を editable モードでインストール
RUN mkdir -p /opt/backend_shared
COPY ./backend_shared /opt/backend_shared
RUN pip install -e /opt/backend_shared

USER workeruser
COPY --chown=workeruser:workeruser ./forecast_worker/app /worker/app
COPY --chown=workeruser:workeruser ./forecast_worker/infra /worker/infra
COPY --chown=workeruser:workeruser ./forecast_worker/domain /worker/domain

WORKDIR /worker
CMD ["python", "-m", "app.worker"]

# ──────────────────────────────────────────────────────────────
# Stage: prod (wheel からインストール、イミュータブル)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS prod
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/worker

WORKDIR /worker

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      libpq5 && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m workeruser

COPY --from=wheelbuilder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

USER workeruser
COPY --chown=workeruser:workeruser ./forecast_worker/app /worker/app
COPY --chown=workeruser:workeruser ./forecast_worker/infra /worker/infra
COPY --chown=workeruser:workeruser ./forecast_worker/domain /worker/domain

WORKDIR /worker
CMD ["python", "-m", "app.worker"]
