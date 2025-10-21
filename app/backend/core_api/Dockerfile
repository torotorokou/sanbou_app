# =========================
# core_api multi-stage
# context: app/backend/core_api (サービス直下)
# =========================

FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /build/requirements.txt
COPY ./requirements-dev.txt /build/requirements-dev.txt
ARG INSTALL_DEV=false
RUN pip install --upgrade pip \
    && pip wheel --no-deps -r /build/requirements.txt -w /wheels \
    && if [ "$INSTALL_DEV" = "true" ]; then pip wheel --no-deps -r /build/requirements-dev.txt -w /wheels; fi

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/backend PATH="/home/appuser/.local/bin:${PATH}"
WORKDIR /backend

RUN useradd -m appuser
USER appuser

COPY --from=builder /wheels /wheels
COPY ./requirements.txt /backend/requirements.txt
COPY ./requirements-dev.txt /backend/requirements-dev.txt
ARG INSTALL_DEV=false
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
USER appuser
RUN pip install --no-cache-dir /wheels/*.whl \
    && if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

# アプリコード
COPY --chown=appuser:appuser ./app /backend/app
COPY --chown=appuser:appuser ./migrations /backend/migrations
COPY --chown=appuser:appuser ./alembic.ini /backend/alembic.ini

USER root
RUN mkdir -p /backend/app/data \
    && chown -R appuser:appuser /backend/app/data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
