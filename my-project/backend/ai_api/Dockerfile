## syntax=docker/dockerfile:1.6
# =========================
# ai_api FastAPI multi-stage build
# builder: wheel ビルド / runtime: slim + 非root
# =========================

FROM python:3.11-slim AS builder
ARG SERVICE_DIR=ai_api
ENV PYTHONDONTWRITEBYTECODE=1 \
		PYTHONUNBUFFERED=1 \
		PIP_NO_CACHE_DIR=1
WORKDIR /wheels

# システム依存ライブラリが必要ならここで (現状なし)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
		&& rm -rf /var/lib/apt/lists/*

COPY ${SERVICE_DIR}/requirements.txt requirements.txt
# Wheel 化 (キャッシュ利用)
RUN --mount=type=cache,target=/root/.cache/pip \
		pip wheel --no-deps -r requirements.txt -w /wheels

# 共有モジュール / アプリ本体は runtime へ直接コピーするためここでは不要

FROM python:3.11-slim AS runtime
ARG SERVICE_DIR=ai_api
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
COPY ${SERVICE_DIR}/requirements.txt ./requirements.txt
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
	&& rm -rf /var/lib/apt/lists/*
USER appuser
RUN pip install --no-cache-dir /wheels/*.whl

# アプリコード / 共有コード
COPY backend_shared/ /backend/backend_shared
COPY ${SERVICE_DIR}/app /backend/app
# COPY config /backend/config

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
