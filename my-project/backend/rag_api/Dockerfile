FROM python:3.10-slim

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    && curl -sSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update && apt-get install -y google-cloud-sdk \
    && apt-get clean

RUN mkdir -p /root/.config/gcloud

WORKDIR /backend

# 依存関係（サービス配下）
COPY rag_api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 共有モジュールを同梱
COPY backend_shared/ /backend/backend_shared

# サービスのアプリ・設定・スクリプトを配置
COPY rag_api/app /backend/app
COPY rag_api/config /backend/config
COPY rag_api/local_data /backend/local_data
COPY rag_api/static /backend/static
COPY rag_api/startup.sh /backend/startup.sh

ENV PYTHONPATH=/backend

# startup.shに実行権限
RUN chmod +x /backend/startup.sh

CMD ["bash", "startup.sh"]
