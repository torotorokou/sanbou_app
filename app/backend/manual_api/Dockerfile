## syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS builder
ARG SERVICE_DIR=manual_api
ARG BASE_PATH=backend
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1
WORKDIR /wheels

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
	&& rm -rf /var/lib/apt/lists/*

COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
	pip wheel --no-deps -r requirements.txt -w /wheels

FROM python:3.11-slim AS runtime
ARG SERVICE_DIR=manual_api
ARG BASE_PATH=backend
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PYTHONPATH=/backend \
	PATH="/home/appuser/.local/bin:${PATH}"
WORKDIR /backend

RUN useradd -m appuser
USER appuser

# deps
COPY --from=builder /wheels /wheels
COPY ${BASE_PATH}/${SERVICE_DIR}/requirements.txt ./requirements.txt
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
	&& rm -rf /var/lib/apt/lists/*
USER appuser
RUN pip install --no-cache-dir /wheels/*.whl

# app
COPY ${BASE_PATH}/${SERVICE_DIR}/app /backend/app
COPY ${BASE_PATH}/${SERVICE_DIR}/startup.sh /backend/startup.sh
USER root
RUN chmod +x /backend/startup.sh && chown appuser:appuser /backend/startup.sh
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health >/dev/null || exit 1

CMD ["bash", "startup.sh"]
