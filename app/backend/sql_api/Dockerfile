## syntax=docker/dockerfile:1.6
# =========================
# sql_api multi-stage
# =========================

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build
ARG SERVICE_DIR=sql_api
ARG BASE_PATH=backend
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt requirements.txt
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements-dev.txt requirements-dev.txt
ARG INSTALL_DEV=false
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN --mount=type=cache,target=/root/.cache/pip \
        pip wheel --no-deps -r requirements.txt -w /wheels \
        && if [ "$INSTALL_DEV" = "true" ]; then pip wheel --no-deps -r requirements-dev.txt -w /wheels; fi

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/backend PATH="/home/appuser/.local/bin:${PATH}"
WORKDIR /backend
ARG SERVICE_DIR=sql_api
ARG BASE_PATH=backend
RUN useradd -m appuser
USER appuser

COPY --from=builder /wheels /wheels
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt requirements.txt
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements-dev.txt requirements-dev.txt
ARG INSTALL_DEV=false
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
USER appuser
RUN pip install --no-cache-dir /wheels/*.whl \
    && if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

# backend_shared を editable install（dev 環境で即反映）
COPY ${BASE_PATH}/backend_shared/ /opt/backend_shared
RUN pip install --no-cache-dir -e /opt/backend_shared

COPY ${BASE_PATH}/${SERVICE_DIR}/app /backend/app
COPY config /backend/config
# 必要な書き込み用ディレクトリ（エンドポイントで os.makedirs するパス）を事前作成し権限付与
USER root
RUN mkdir -p /backend/app/data/syogun_csv \
    && chown -R appuser:appuser /backend/app/data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
