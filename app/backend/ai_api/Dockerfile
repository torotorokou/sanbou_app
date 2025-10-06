## syntax=docker/dockerfile:1.6
# =========================
# ai_api FastAPI multi-stage build
# builder: wheel ビルド / runtime: slim + 非root
# =========================

# --- Example for production build (wheel install) ---
# 本番環境では backend_shared を wheel 化してインストールすることで固定バージョン配布が可能
# 現在は editable install で開発環境に最適化されています
#
# FROM python:3.11-slim AS build_shared
# WORKDIR /build
# COPY backend/backend_shared/ ./backend_shared/
# RUN pip install -U build && python -m build backend_shared
#
# FROM python:3.11-slim AS builder
# ARG SERVICE_DIR=ai_api
# ARG BASE_PATH=backend
# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# WORKDIR /wheels
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
#     && rm -rf /var/lib/apt/lists/*
# COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt requirements.txt
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip wheel --no-deps -r requirements.txt -w /wheels
#
# FROM python:3.11-slim AS runtime
# ARG SERVICE_DIR=ai_api
# ARG BASE_PATH=backend
# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/backend
# WORKDIR /backend
# RUN useradd -m appuser
# USER appuser
# COPY --from=builder /wheels /wheels
# COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt requirements.txt
# USER root
# RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
#     && rm -rf /var/lib/apt/lists/*
# USER appuser
# RUN pip install --no-cache-dir /wheels/*.whl
# COPY --from=build_shared /build/backend_shared/dist/*.whl /tmp/
# RUN pip install --no-cache-dir /tmp/backend_shared-*.whl
# COPY ${BASE_PATH}/${SERVICE_DIR}/app /backend/app
# COPY config /backend/config
# EXPOSE 8000
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# --- End of production example ---

FROM python:3.11-slim AS builder
ARG SERVICE_DIR=ai_api
ARG BASE_PATH=backend
ENV PYTHONDONTWRITEBYTECODE=1 \
		PYTHONUNBUFFERED=1 \
		PIP_NO_CACHE_DIR=1
WORKDIR /wheels

# システム依存ライブラリが必要ならここで (現状なし)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
		&& rm -rf /var/lib/apt/lists/*

COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt requirements.txt
# Wheel 化 (キャッシュ利用)
RUN --mount=type=cache,target=/root/.cache/pip \
		pip wheel --no-deps -r requirements.txt -w /wheels

# 共有モジュール / アプリ本体は runtime へ直接コピーするためここでは不要

FROM python:3.11-slim AS runtime
ARG SERVICE_DIR=ai_api
ARG BASE_PATH=backend
ENV PYTHONDONTWRITEBYTECODE=1 \
		PYTHONUNBUFFERED=1 \
		PYTHONPATH=/backend \
		PATH="/home/appuser/.local/bin:${PATH}"
WORKDIR /backend

# 非rootユーザー
RUN useradd -m appuser
USER appuser

# 依存インストール
COPY --from=builder /wheels /wheels
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt ./requirements.txt
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
	&& rm -rf /var/lib/apt/lists/*
USER appuser
RUN pip install --no-cache-dir /wheels/*.whl

# backend_shared を editable install（dev 環境で即反映）
COPY ${BASE_PATH}/backend_shared/ /opt/backend_shared
RUN pip install --no-cache-dir -e /opt/backend_shared

# アプリコード
COPY ${BASE_PATH}/${SERVICE_DIR}/app /backend/app
COPY config /backend/config

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
