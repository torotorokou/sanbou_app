FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/worker

WORKDIR /worker

# Install dependencies
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY app /worker/app
COPY infra /worker/infra
COPY domain /worker/domain

# Create non-root user
RUN useradd -m workeruser
USER workeruser

WORKDIR /worker
CMD ["python", "-m", "app.worker"]
