# Dockerfile

FROM node:20-slim

# 作業ディレクトリ（中で /app/my-project に入る）
WORKDIR /app

RUN apt-get update && \
    apt-get install -y git curl unzip zip && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 5173

CMD ["bash"]
