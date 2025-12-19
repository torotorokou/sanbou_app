# Minimal runtime image for daily/weekly inference
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Tokyo

# System deps for scientific stack and possible model backends
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc g++ \
      libgomp1 \
      ca-certificates \
      tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer cache)
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project (scripts + data placeholders)
COPY ./scripts ./scripts
COPY ./data ./data

# Default command: print quick help
CMD ["bash", "-lc", "echo 'Container ready. Try: python scripts/daily_tplus1_predict.py --help' && ls -1 scripts"]
