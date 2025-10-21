# =========================
# manual_api multi-stage
# context: app/backend/manual_api (サービス直下)
# =========================

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /build/requirements.txt
RUN pip install --upgrade pip \
    && pip wheel --no-deps -r /build/requirements.txt -w /wheels

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend \
    PATH="/home/appuser/.local/bin:${PATH}"
WORKDIR /backend

RUN useradd -m appuser
USER appuser

COPY --from=builder /wheels /wheels
COPY ./requirements.txt /backend/requirements.txt
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
USER appuser
RUN pip install --no-cache-dir /wheels/*.whl

# アプリコード
COPY --chown=appuser:appuser ./app /backend/app
COPY --chown=appuser:appuser ./data /backend/data
COPY --chown=appuser:appuser --chmod=0755 ./startup.sh /backend/startup.sh

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["bash", "startup.sh"]
