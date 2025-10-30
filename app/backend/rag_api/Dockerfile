# =========================
# rag_api Dockerfile (multi-stage: wheelbuilder/dev/prod)
# Context: app/backend
# =========================

# ──────────────────────────────────────────────────────────────
# Stage: base (gcloud SDK インストール)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl gnupg lsb-release ca-certificates build-essential && \
    curl -sSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-cloud-sdk && \
    rm -rf /var/lib/apt/lists/*

# ──────────────────────────────────────────────────────────────
# Stage: wheelbuilder
# ──────────────────────────────────────────────────────────────
FROM base AS wheelbuilder
COPY ./backend_shared /build/backend_shared
RUN pip install --upgrade pip setuptools wheel && \
    cd /build/backend_shared && \
    pip wheel --no-deps . -w /wheels

COPY ./rag_api/requirements.txt /build/requirements.txt
RUN pip wheel --no-deps -r /build/requirements.txt -w /wheels

# ──────────────────────────────────────────────────────────────
# Stage: dev (ホットリロード対応)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS dev
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend:/opt/backend_shared/src

WORKDIR /backend

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      ca-certificates \
      build-essential \
      git && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 -s /bin/bash appuser

# gcloud SDK コピー
COPY --from=base /usr/lib/google-cloud-sdk /usr/lib/google-cloud-sdk
ENV PATH="/usr/lib/google-cloud-sdk/bin:${PATH}"

COPY ./rag_api/requirements.txt /backend/requirements.txt
RUN pip install --no-cache-dir -r /backend/requirements.txt watchfiles

# backend_shared を editable モードでインストール
RUN mkdir -p /opt/backend_shared
COPY ./backend_shared /opt/backend_shared
RUN pip install -e /opt/backend_shared

# USER 切替前に必要ディレクトリを作成・chown
RUN mkdir -p /backend/app /backend/test /backend/static/pdfs /backend/static/test_pdfs \
             /backend/local_data /home/appuser/.config/gcloud && \
    chown -R appuser:appuser /backend /opt/backend_shared /home/appuser/.config

USER appuser
COPY --chown=appuser:appuser ./rag_api/app /backend/app
COPY --chown=appuser:appuser --chmod=0755 ./rag_api/startup.sh /backend/startup.sh

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["bash", "startup.sh"]

# ──────────────────────────────────────────────────────────────
# Stage: prod (wheel からインストール、イミュータブル)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS prod
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend

WORKDIR /backend

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 -s /bin/bash appuser

# gcloud SDK コピー
COPY --from=base /usr/lib/google-cloud-sdk /usr/lib/google-cloud-sdk
ENV PATH="/usr/lib/google-cloud-sdk/bin:${PATH}"

COPY --from=wheelbuilder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

# USER 切替前に必要ディレクトリを作成・chown
RUN mkdir -p /backend/app /backend/test /backend/static/pdfs /backend/static/test_pdfs \
             /backend/local_data /home/appuser/.config/gcloud && \
    chown -R appuser:appuser /backend /home/appuser/.config

USER appuser
COPY --chown=appuser:appuser ./rag_api/app /backend/app
COPY --chown=appuser:appuser --chmod=0755 ./rag_api/startup.sh /backend/startup.sh

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["bash", "startup.sh"]
