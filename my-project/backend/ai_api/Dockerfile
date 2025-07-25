FROM python:3.10-slim

# 作業ディレクトリを /app に設定
WORKDIR /backend

# requirements をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app ディレクトリ全体を /backend/app にコピー
COPY ./app /backend/app

ENV PYTHONPATH=/backend

# ✅ 正しい import path を指定（/backend/app/main.py → app.main）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
