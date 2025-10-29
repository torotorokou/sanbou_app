# =========================
# plan_worker Dockerfile (multi-stage: dev/prod)
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

COPY ./backend_shared /build/backend_shared
RUN pip install --upgrade pip setuptools wheel && \
    cd /build/backend_shared && \
    pip wheel --no-deps . -w /wheels

COPY ./plan_worker/requirements.txt /build/requirements.txt
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
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m appuser

COPY ./plan_worker/requirements.txt /backend/requirements.txt
RUN pip install --no-cache-dir -r /backend/requirements.txt

# backend_shared を editable モードでインストール
RUN mkdir -p /opt/backend_shared
COPY ./backend_shared /opt/backend_shared
RUN pip install -e /opt/backend_shared

USER appuser
COPY --chown=appuser:appuser ./plan_worker/app /backend/app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["python", "-m", "app.worker"]

# ──────────────────────────────────────────────────────────────
# Stage: prod (wheel からインストール、イミュータブル)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS prod
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend

WORKDIR /backend

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m appuser

COPY --from=wheelbuilder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

USER appuser
COPY --chown=appuser:appuser ./plan_worker/app /backend/app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["python", "-m", "app.worker"]

