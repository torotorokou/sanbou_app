FROM python:3.10-slim

WORKDIR /backend

# 依存関係のインストール（サービス固有）
COPY ai_api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 共有モジュールを同梱
COPY backend_shared/ /backend/backend_shared

# サービスのアプリ本体と設定を配置
COPY ai_api/app /backend/app
COPY ai_api/config /backend/config

ENV PYTHONPATH=/backend

# FastAPI 起動（reload は本番では無視されるが統一）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
