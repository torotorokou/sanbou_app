## syntax=docker/dockerfile:1.6
# =========================
# rag_api multi-stage
# gcloud SDK が必要: builder でインストールし runtime へ最小コピー
# =========================

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg lsb-release ca-certificates \
    && curl -sSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update && apt-get install -y --no-install-recommends google-cloud-sdk build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip wheel --no-deps -r requirements.txt -w /wheels

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/backend PATH="/home/appuser/.local/bin:${PATH}"
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
COPY requirements.txt ./requirements.txt
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
USER appuser
RUN pip install --no-cache-dir /wheels/*.whl

USER appuser
COPY backend_shared/ /backend/backend_shared
COPY app /backend/app
# COPY config /backend/config
COPY startup.sh /backend/startup.sh
USER root
RUN chmod +x /backend/startup.sh && chown appuser:appuser /backend/startup.sh
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["bash", "startup.sh"]
