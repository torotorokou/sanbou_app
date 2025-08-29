## Multi-stage build: build React (Vite) then serve with Nginx
## 用途: stg/prod など本番系で "Welcome to nginx!" を回避し常に dist を同梱

### 1) Build stage (Node) - use Debian variant to simplify native module (canvas) build
FROM node:20-bullseye AS build
WORKDIR /app

# Install build deps for node-canvas (needs Python, pkg-config, cairo, pango, jpeg, gif, librsvg, etc.)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
		apt-get install -y --no-install-recommends \
			python3 make g++ pkg-config \
			libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev \
		&& rm -rf /var/lib/apt/lists/*

# 依存関係のみ先にコピー (キャッシュ有効活用)
COPY frontend/package*.json ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi

# ソース一式をコピーしてビルド
COPY frontend/ .
RUN npm run build

### 2) Runtime stage (Nginx)
FROM nginx:1.27-alpine AS runtime

# Nginx のカスタム設定 (conf.d 全置換)
COPY nginx/conf.d /etc/nginx/conf.d
COPY nginx/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# React ビルド成果物を配置
COPY --from=build /app/dist /usr/share/nginx/html

# (Optional) If size is critical, consider a slimmer build stage or copying only needed node_modules for a secondary build.

# 健康チェック用 (任意) - statically served file 確認
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD [ -f /usr/share/nginx/html/index.html ] || exit 1

EXPOSE 80 443
ENTRYPOINT ["/entrypoint.sh"]
