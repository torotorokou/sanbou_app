## =============================================================
## Dockerfile for inbound_forecast_api (需要予測APIサービス)
## - 標準化されたバックエンドビルドパターンに準拠
## - 開発用(dev)ターゲットでホットリロード対応
## =============================================================

# === Stage 1: Base ===
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Tokyo

# System deps for scientific stack (pandas, sklearn, lightgbm, etc.)
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc g++ \
      libgomp1 \
      ca-certificates \
      tzdata \
      curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /backend

# Install Python deps first (better layer cache)
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# === Stage 2: Development ===
FROM base AS dev

# Install development tools
RUN pip install --no-cache-dir watchfiles

# Copy application code (will be mounted as volume in dev)
COPY ./app ./app
COPY ./scripts ./scripts
COPY ./data ./data
COPY ./models ./models
COPY ./output ./output
COPY ./worker ./worker

# Set PYTHONPATH for Clean Architecture
ENV PYTHONPATH=/backend

# Non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /backend
USER appuser

# Healthcheck endpoint (FastAPI /health)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default: Start FastAPI server (can be overridden in compose)
CMD ["uvicorn", "scripts.api_server:app", "--host", "0.0.0.0", "--port", "8000"]

# === Stage 3: Production ===
FROM base AS prod

# Copy application code
COPY ./app ./app
COPY ./scripts ./scripts
COPY ./data ./data
COPY ./models ./models
COPY ./output ./output
COPY ./worker ./worker

# Set PYTHONPATH for Clean Architecture
ENV PYTHONPATH=/backend

# Non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /backend
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["uvicorn", "scripts.api_server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
