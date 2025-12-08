# =========================
# ai_api Dockerfile (multi-stage: wheelbuilder/base/dev/stg/prod)
# Context: app/backend
# 
# Target stages:
#   - wheelbuilder: Python 依存パッケージをビルド (wheel 生成)
#   - base: 共通ランタイムベース (wheelインストール + アプリコード配置)
#   - dev: ローカル開発用 (ホットリロード有効、editable install)
#   - stg: ステージング環境用 (base継承、AUTH_MODE=vpn_dummy 等の環境変数)
#   - prod: 本番環境用 (base継承、AUTH_MODE=iap 等の環境変数)
# =========================

# ──────────────────────────────────────────────────────────────
# Stage: wheelbuilder
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS wheelbuilder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Security: Update OS packages to patch vulnerabilities
# Security: Upgrade pip to latest version to fix CVE-2025-8869
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY ./backend_shared /build/backend_shared
RUN python -m pip install --upgrade "pip>=25.3,<26.0" setuptools wheel && \
    cd /build/backend_shared && \
    pip wheel --no-deps . -w /wheels

COPY ./ai_api/requirements.txt /build/requirements.txt
RUN pip wheel --no-deps -r /build/requirements.txt -w /wheels

# ──────────────────────────────────────────────────────────────
# Stage: dev (ホットリロード対応)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS dev
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend:/opt/backend_shared/src

WORKDIR /backend

# Security: Update OS packages to patch vulnerabilities
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      curl \
      ca-certificates \
      build-essential \
      git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 -s /bin/bash appuser

COPY ./ai_api/requirements.txt /backend/requirements.txt
# Security: Upgrade pip to >=25.3 to fix CVE-2025-8869
RUN python -m pip install --upgrade "pip>=25.3,<26.0" && \
    pip install --no-cache-dir -r /backend/requirements.txt watchfiles

# backend_shared を editable モードでインストール
RUN mkdir -p /opt/backend_shared
COPY ./backend_shared /opt/backend_shared
RUN pip install -e /opt/backend_shared

# USER 切替前に必要ディレクトリを作成・chown
RUN mkdir -p /backend/app /backend/test && \
    chown -R appuser:appuser /backend /opt/backend_shared

USER appuser
COPY --chown=appuser:appuser ./ai_api/app /backend/app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--reload", "--reload-dir", "/backend/app", "--reload-dir", "/opt/backend_shared/src"]

# ──────────────────────────────────────────────────────────────
# Stage: base (wheel からインストール、イミュータブル)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend

WORKDIR /backend

# Security: Update OS packages to patch vulnerabilities
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      curl \
      ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 -s /bin/bash appuser

COPY --from=wheelbuilder /wheels /wheels
# Security: Upgrade pip to >=25.3 to fix CVE-2025-8869
RUN python -m pip install --upgrade "pip>=25.3,<26.0" && \
    pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

# USER 切替前に必要ディレクトリを作成・chown
RUN mkdir -p /backend/app /backend/test && \
    chown -R appuser:appuser /backend

USER appuser
COPY --chown=appuser:appuser ./ai_api/app /backend/app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ──────────────────────────────────────────────────────────────
# Stage: stg (ステージング環境用 - VPN 経由アクセス)
# ──────────────────────────────────────────────────────────────
FROM base AS stg
ENV APP_ENV=stg

# ──────────────────────────────────────────────────────────────
# Stage: prod (本番環境用 - LB + IAP 経由)
# ──────────────────────────────────────────────────────────────
FROM base AS prod
ENV APP_ENV=prod
