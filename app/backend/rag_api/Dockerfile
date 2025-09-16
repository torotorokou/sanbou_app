## syntax=docker/dockerfile:1.6
# =========================
# rag_api multi-stage
# gcloud SDK が必要: builder でインストールし runtime へ最小コピー
# =========================

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build
ARG SERVICE_DIR=rag_api
ARG BASE_PATH=backend
RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg lsb-release ca-certificates \
    && curl -sSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update && apt-get install -y --no-install-recommends google-cloud-sdk build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip wheel --no-deps -r requirements.txt -w /wheels

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/backend PATH="/home/appuser/.local/bin:${PATH}"
WORKDIR /backend
ARG SERVICE_DIR=rag_api
ARG BASE_PATH=backend
RUN useradd -m appuser
USER appuser

# gcloud の必要最小限 (サイズ削減のため丸ごとコピー。将来は slim SDK へ差し替え検討)
USER root
COPY --from=builder /usr/lib/google-cloud-sdk /usr/lib/google-cloud-sdk
ENV PATH="/usr/lib/google-cloud-sdk/bin:${PATH}"
RUN mkdir -p /home/appuser/.config/gcloud && chown -R appuser:appuser /home/appuser/.config

# deps
COPY --from=builder /wheels /wheels
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt requirements.txt
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
USER appuser
RUN pip install --no-cache-dir /wheels/*.whl

USER appuser
COPY ${BASE_PATH}/backend_shared/ /backend/backend_shared
COPY ${BASE_PATH}/${SERVICE_DIR}/app /backend/app
COPY ${BASE_PATH}/${SERVICE_DIR}/startup.sh /backend/startup.sh
COPY config /backend/config
USER root
RUN chmod +x /backend/startup.sh && chown appuser:appuser /backend/startup.sh
USER appuser

# static 配信ディレクトリを先に作成 & 所有権付与（実行時 PermissionError 対策）
USER root
RUN mkdir -p /backend/static/pdfs /backend/static/test_pdfs \
    && chown -R appuser:appuser /backend/static
USER appuser

# Ensure /backend/local_data is writable to avoid fallback to /home
USER root
RUN mkdir -p /backend/local_data \
    && chown -R appuser:appuser /backend/local_data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["bash", "startup.sh"]
