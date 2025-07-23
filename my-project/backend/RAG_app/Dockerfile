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

# 作業ディレクトリ
WORKDIR /app

# 必要ファイルコピー
COPY . .

# Pythonパッケージインストール
RUN pip install --no-cache-dir -r requirements.txt

# スタートアップスクリプト実行
CMD ["bash", "startup.sh"]
