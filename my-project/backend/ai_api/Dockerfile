FROM python:3.10-slim

# 作業ディレクトリを /app に設定
WORKDIR /app

# requirements をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app ディレクトリ全体を /app/app にコピー
COPY ./app ./app

# ✅ 正しい import path を指定（/app/app/main.py → app.main）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
