## syntax=docker/dockerfile:1.6
# =========================
# Frontend (React/Vite) Multi-stage
# builder: node:20-slim で依存取得+ビルド
# runtime: nginx:alpine に dist のみ配置
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

# 非 root 実行 (nginx:alpine には 'nginx' ユーザーが存在)
USER nginx
WORKDIR /usr/share/nginx/html

# ビルド成果物のみコピー
COPY --from=builder /app/dist ./

# Nginx デフォルト設定で SPA 404 -> index.html フォールバックするよう簡易設定
USER root
RUN printf 'try_files $uri /index.html;\n' > /tmp/rewrite.conf \
    && sed -i 's|location / {|location / { try_files $uri $uri/ /index.html;|g' /etc/nginx/conf.d/default.conf || true \
    && awk 'FNR==NR{a[NR]=$0;next}1;END{print "\n# inserted: spa fallback";for(i in a)print a[i]}' /tmp/rewrite.conf /etc/nginx/conf.d/default.conf >/tmp/new && mv /tmp/new /etc/nginx/conf.d/default.conf \
    && chown -R nginx:nginx /usr/share/nginx/html
USER nginx

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -q -O /dev/null http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

# =========================
# Dev stage (Node runtime with hot reload)
# docker-compose.override.yml で target=dev を指定して利用
# ソースをボリュームマウントした際 node_modules が無い場合は起動前に npm ci を実行
# =========================
FROM node:20-slim AS dev
WORKDIR /app
COPY package.json package-lock.json* ./
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN npm ci || true
# 開発時はホスト側を /app にマウントするため依存が消えるケースがあるので起動前チェック
EXPOSE 5173
CMD ["bash", "-c", "set -e; if [ ! -d node_modules ]; then echo '[dev] node_modules missing -> npm ci'; npm ci; fi; npm run dev -- --host 0.0.0.0"]
