# =========================
# rag_api multi-stage
# context: app/backend/rag_api (サービス直下)
# gcloud SDK が必要: builder でインストールし runtime へ最小コピー
# =========================

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg lsb-release ca-certificates build-essential \
    && curl -sSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update && apt-get install -y --no-install-recommends google-cloud-sdk \
    && rm -rf /var/lib/apt/lists/*

# backend_sharedのビルド
COPY ./backend_shared /build/backend_shared
# README.mdを作成（pyproject.tomlで必要）
RUN touch /build/backend_shared/README.md || true
RUN cd /build/backend_shared && pip wheel --no-deps . -w /wheels

COPY ./rag_api/requirements.txt /build/requirements.txt
RUN pip install --upgrade pip \
    && pip wheel --no-deps -r /build/requirements.txt -w /wheels

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/backend:/opt/backend_shared/src PATH="/home/appuser/.local/bin:${PATH}"
WORKDIR /backend
RUN useradd -m appuser
USER appuser

# gcloud の必要最小限 (サイズ削減のため丸ごとコピー。将来は slim SDK へ差し替え検討)
USER root
COPY --from=builder /usr/lib/google-cloud-sdk /usr/lib/google-cloud-sdk
ENV PATH="/usr/lib/google-cloud-sdk/bin:${PATH}"
RUN mkdir -p /home/appuser/.config/gcloud && chown -R appuser:appuser /home/appuser/.config

# deps
COPY --from=builder /wheels /wheels
COPY ./rag_api/requirements.txt /backend/requirements.txt
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
USER appuser
RUN pip install --no-cache-dir /wheels/*.whl

# アプリコード
COPY --chown=appuser:appuser ./rag_api/app /backend/app
COPY --chown=appuser:appuser --chmod=0755 ./rag_api/startup.sh /backend/startup.sh

# static 配信ディレクトリを先に作成 & 所有権付与（実行時 PermissionError 対策）
USER root
RUN mkdir -p /backend/static/pdfs /backend/static/test_pdfs \
    && chown -R appuser:appuser /backend/static

# Ensure /backend/local_data is writable to avoid fallback to /home
RUN mkdir -p /backend/local_data \
    && chown -R appuser:appuser /backend/local_data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["bash", "startup.sh"]
