FROM node:20-bullseye

# --- 必須：開発に必要なツールを追加 ---
RUN apt-get update && apt-get install -y sudo bash git curl \
    && rm -rf /var/lib/apt/lists/*

# --- ✅ nodeユーザーを作成（UID 1000で VSCode と一致） ---
RUN id node 2>/dev/null || useradd -m -s /bin/bash -u 1000 node \
    && echo 'node ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# --- 作業ディレクトリの準備と権限設定 ---
RUN mkdir -p /app && chown -R node:node /app

# --- nodeユーザーに切り替え ---
USER node
WORKDIR /app

# --- 依存関係インストール（react-pdf / pdfjs-dist 含む） ---
COPY --chown=node:node package.json package-lock.json* ./

# react-pdf が package.json に無い場合の保険的に明示的に追加（任意）
# RUN npm install react-pdf pdfjs-dist

RUN npm install

# --- アプリ全体をコピー ---
COPY --chown=node:node . .

# ✅ pdf.worker.min.js を public にダウンロード（バージョン固定）
RUN curl -o public/pdf.worker.min.js https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js

EXPOSE 5173

# --- Vite起動 ---
CMD ["npx", "vite", "--host", "0.0.0.0"]
