## =============================================================================
## Multi-stage build: Build React (Vite) then serve with Nginx
## For STG/PROD environments
## =============================================================================
## nginx 設定ファイルのマッピング:
##   - STG: conf.d/stg.conf → /etc/nginx/conf.d/ にコピー
##   - PROD: conf.d/prod.conf → /etc/nginx/conf.d/ にコピー
##   - 実行時は docker-compose.{stg,prod}.yml の volumes で上書き可能
##
## ★ 重要: VM 側 nginx は HTTP(80) のみで応答する構成
##   - HTTPS へのリダイレクトは行いません
##   - ドメイン・TLS は GCP LB + IAP 側で終端します
## =============================================================================

# =============================================================================
# Stage 1: Build React application
# =============================================================================
FROM node:20-bullseye AS build
WORKDIR /app

# Install dependencies for node-canvas (Python, cairo, pango, etc.)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
        python3 make g++ pkg-config \
        libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js dependencies (cache layer)
COPY frontend/package*.json ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi

# Build React application
COPY frontend/ .
RUN npm run build

# =============================================================================
# Stage 2: Nginx runtime (STG)
# =============================================================================
FROM nginx:1.27-alpine AS stg

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy nginx configuration files for STG
COPY nginx/conf.d/_proxy_common.conf /etc/nginx/conf.d/
COPY nginx/conf.d/stg.conf /etc/nginx/conf.d/

# Copy React build artifacts
COPY --from=build /app/dist /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD [ -f /usr/share/nginx/html/index.html ] || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# =============================================================================
# Stage 3: Nginx runtime (PROD)
# =============================================================================
FROM nginx:1.27-alpine AS prod

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy nginx configuration files for PROD
COPY nginx/conf.d/_proxy_headers.conf /etc/nginx/conf.d/
COPY nginx/conf.d/prod.conf /etc/nginx/conf.d/

# Copy React build artifacts
COPY --from=build /app/dist /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD [ -f /usr/share/nginx/html/index.html ] || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
