# =========================
# Frontend (React/Vite) Multi-stage
# Target stages:
#   - builder: node:20-slim で依存取得+ビルド
#   - base: nginx:alpine に dist のみ配置（共通ベース）
#   - stg: ステージング環境用（base継承）
#   - prod: 本番環境用（base継承）
#   - dev: ローカル開発用（ホットリロード）
#
# ★ 注意: このイメージは nginx ベースですが、nginx 設定は含まれていません
#   - nginx 設定は別途 app/nginx/Dockerfile でビルドされます
#   - stg/prod 用の nginx イメージは app/nginx/Dockerfile → docker/docker-compose.{stg,prod}.yml で使用
#   - このイメージは主にローカル開発(dev stage)で使用されます
# =========================

FROM node:20-slim AS builder
# NODE_ENV は build 時 devDependencies 必須 (tsc, vite) のため未設定
WORKDIR /app

# 依存レイヤーのキャッシュ最適化
COPY package.json package-lock.json* ./
# curl が slim に含まれないため追加
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN npm ci

# ソースコピー（test関連は .dockerignore で除外: tests/, *.spec.*, *.test.*, vitest.config.* など）
COPY . .

# Vite ビルド（環境変数は compose 側で注入想定）
RUN npm run build

FROM nginx:1.27-alpine AS base
LABEL org.opencontainers.image.source="https://example.local/sanbou_app" \
            org.opencontainers.image.description="Sanbou frontend base (nginx)"

# base は root のまま (公式 entrypoint が /var/cache/nginx/* を作成するため必要)
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
# Stage: stg (ステージング環境用 - VPN 経由アクセス)
# =========================
FROM base AS stg
# ステージング環境固有の設定（必要に応じて追加）
ENV APP_ENV=stg

# =========================
# Stage: prod (本番環境用 - LB + IAP 経由)
# =========================
FROM base AS prod
# 本番環境固有の設定（必要に応じて追加）
ENV APP_ENV=prod

# =========================
# Alias: runtime (後方互換性のため base を参照)
# =========================
FROM base AS runtime

# =========================
# Dev stage (ホットリロード用)
# =========================
FROM node:20-slim AS dev
WORKDIR /app

# 依存インストールスクリプトの作成
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
