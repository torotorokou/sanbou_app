# =========================
# ai_api FastAPI multi-stage build
# context: app/backend/ai_api (サービス直下)
# =========================

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# backend_sharedのビルド
COPY ./backend_shared /build/backend_shared
# README.mdを作成（pyproject.tomlで必要）
RUN touch /build/backend_shared/README.md || true
RUN cd /build/backend_shared && pip wheel --no-deps . -w /wheels

COPY ./ai_api/requirements.txt /build/requirements.txt
RUN pip install --upgrade pip \
    && pip wheel --no-deps -r /build/requirements.txt -w /wheels

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend:/opt/backend_shared/src \
    PATH="/home/appuser/.local/bin:${PATH}"
WORKDIR /backend

RUN useradd -m appuser
USER appuser

COPY --from=builder /wheels /wheels
COPY ./ai_api/requirements.txt /backend/requirements.txt
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
USER appuser
RUN pip install --no-cache-dir /wheels/*.whl

# アプリコード
COPY --chown=appuser:appuser ./ai_api/app /backend/app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
