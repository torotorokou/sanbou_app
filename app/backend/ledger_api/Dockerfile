# =========================
# ledger_api Dockerfile (multi-stage: wheelbuilder/dev/prod)
# Context: app/backend
# =========================

# ──────────────────────────────────────────────────────────────
# Stage: wheelbuilder
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS wheelbuilder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      curl && \
    rm -rf /var/lib/apt/lists/*

COPY ./backend_shared /build/backend_shared
RUN pip install --upgrade pip setuptools wheel && \
    cd /build/backend_shared && \
    pip wheel --no-deps . -w /wheels

COPY ./ledger_api/requirements.txt /build/requirements.txt
RUN pip wheel --no-deps -r /build/requirements.txt -w /wheels

# ──────────────────────────────────────────────────────────────
# Stage: dev (ホットリロード対応)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS dev
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend:/opt/backend_shared/src \
    BASE_API_DIR=/backend/app

WORKDIR /backend

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libreoffice \
      fonts-noto-cjk fonts-noto-cjk-extra \
      fonts-ipafont-mincho fonts-ipafont-gothic \
      curl \
      ca-certificates \
      build-essential \
      git && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 -s /bin/bash appuser

ENV PATH="/usr/lib/libreoffice/program:${PATH}"

COPY ./ledger_api/requirements.txt /backend/requirements.txt
COPY ./ledger_api/requirements-dev.txt /backend/requirements-dev.txt
RUN pip install --no-cache-dir -r /backend/requirements.txt watchfiles

# backend_shared を editable モードでインストール
RUN mkdir -p /opt/backend_shared
COPY ./backend_shared /opt/backend_shared
RUN pip install -e /opt/backend_shared

# USER 切替前に必要ディレクトリを作成・chown
RUN mkdir -p /backend/app /backend/app/infra/data_sources/input /backend/app/infra/data_sources/output \
             /backend/app/api/logs /backend/test && \
    chown -R appuser:appuser /backend /opt/backend_shared

USER appuser
COPY --chown=appuser:appuser ./ledger_api/app /backend/app
COPY --chown=appuser:appuser --chmod=0755 ./ledger_api/startup.sh /backend/startup.sh

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["/backend/startup.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--reload", "--reload-dir", "/backend/app", "--reload-dir", "/opt/backend_shared/src"]

# ──────────────────────────────────────────────────────────────
# Stage: prod (wheel からインストール、イミュータブル)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS prod
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend \
    BASE_API_DIR=/backend/app

WORKDIR /backend

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libreoffice \
      fonts-noto-cjk fonts-noto-cjk-extra \
      fonts-ipafont-mincho fonts-ipafont-gothic \
      curl \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 -s /bin/bash appuser

ENV PATH="/usr/lib/libreoffice/program:${PATH}"

COPY --from=wheelbuilder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

# USER 切替前に必要ディレクトリを作成・chown
RUN mkdir -p /backend/app /backend/app/infra/data_sources/input /backend/app/infra/data_sources/output \
             /backend/app/api/logs /backend/test && \
    chown -R appuser:appuser /backend

USER appuser
COPY --chown=appuser:appuser ./ledger_api/app /backend/app
COPY --chown=appuser:appuser --chmod=0755 ./ledger_api/startup.sh /backend/startup.sh

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["/backend/startup.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
