## syntax=docker/dockerfile:1.6
# =========================
# Frontend (React/Vite) Multi-stage
# builder: node:20-slim で依存取得+ビルド
# runtime: nginx:alpine に dist のみ配置 (Welcome ページ完全除去)
# =========================

FROM node:20-slim AS builder
# NODE_ENV は build 時 devDependencies 必須 (tsc, vite) のため未設定
WORKDIR /app

# 依存レイヤーのキャッシュ最適化
COPY package.json package-lock.json* ./
# curl が slim に含まれないため追加
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# ソースコピー（テスト等は .dockerignore で除外）
COPY . .
# 外部取得アセット（サイズ小）
RUN mkdir -p public \
 && curl -sSL -o public/pdf.worker.min.js https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js

# Vite ビルド（環境変数は compose 側で注入想定）
RUN npm run build

FROM nginx:1.27-alpine AS runtime
LABEL org.opencontainers.image.source="https://example.local/sanbou_app" \
            org.opencontainers.image.description="Sanbou frontend runtime (nginx)"

# runtime は root のまま (公式 entrypoint が /var/cache/nginx/* を作成するため必要)
USER root
WORKDIR /usr/share/nginx/html
RUN rm -rf ./*
COPY --from=builder /app/dist ./
# 所有権整備
RUN chown -R nginx:nginx /usr/share/nginx/html

# SPA フォールバック (default.conf を前提に書き換えず、別途 conf.d マウントで実現)
# -> conf.d/app.conf 側で try_files を設定するためここで sed ハック不要

# NOTE: セキュリティ上 root 常駐を避けたい場合は別途 /var/cache/nginx 等を事前作成 & chown 後に USER nginx へ変更する hardening を検討
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -q -O /dev/null http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]

# =========================
# Dev stage (ホットリロード用)
# =========================
FROM node:20-slim AS dev
WORKDIR /app
COPY package.json package-lock.json* ./
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN npm ci || true
# エントリポイント: ボリュームで node_modules が空になる場合に備え起動時に依存を整える
RUN printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'cd /app' \
    'if [ "${NODE_ENV:-}" = "production" ] || [ "${npm_config_production:-}" = "true" ]; then' \
    '  echo "[dev-entrypoint] forcing npm_config_production=false for dev"' \
    '  export npm_config_production=false' \
    'fi' \
    'if [ ! -x node_modules/.bin/vite ]; then' \
    '  echo "[dev-entrypoint] installing deps (npm ci)..."' \
    '  if [ -f package-lock.json ]; then npm ci; else npm install; fi' \
    'fi' \
    'exec "$@"' \
    > /usr/local/bin/dev-entrypoint.sh \
    && chmod +x /usr/local/bin/dev-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/dev-entrypoint.sh"]
EXPOSE 5173
# Simplify dev CMD: rely on package.json passing host/port to vite to avoid shell argument parsing issues
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
