# =========================
# plan_worker Dockerfile (simple, single-stage)
# Context: app/backend
# =========================

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/worker

WORKDIR /worker

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m workeruser

# Copy requirements and install (currently minimal)
COPY ./plan_worker/requirements.txt /worker/requirements.txt
RUN pip install --no-cache-dir -r /worker/requirements.txt || true

USER workeruser

# Copy application code
COPY --chown=workeruser:workeruser ./plan_worker/app /worker/app
COPY --chown=workeruser:workeruser ./plan_worker/infra /worker/infra
COPY --chown=workeruser:workeruser ./plan_worker/domain /worker/domain

WORKDIR /worker
CMD ["python", "-m", "app.worker"]

