FROM python:3.10-slim

# 作業ディレクトリ
WORKDIR /backend

# 必要なパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY ./app /backend/app

ENV PYTHONPATH=/backend

# FastAPIアプリ起動（ホットリロード付き）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
