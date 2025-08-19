.PHONY: help \
        up down build restart rebuild logs ps clean-pycache fresh \
        prod-up prod-down prod-build prod-restart prod-rebuild config prod-config

# -----------------------------------
# 設定
# -----------------------------------
COMPOSE_DEV  = docker compose
COMPOSE_PROD = docker compose -f docker-compose.yml

# -----------------------------------
# ヘルプ
# -----------------------------------
help:
	@echo "Dev:"
	@echo "  make up            - 開発: 起動（override 自動適用）"
	@echo "  make down          - 開発: 停止＋ボリューム削除（DB初期化含む）"
	@echo "  make build         - 開発: ノーキャッシュビルド"
	@echo "  make restart       - 開発: down -> build -> up"
	@echo "  make rebuild       - 開発: pycache削除 -> 完全再構築（DB初期化含む）"
	@echo "  make fresh         - 開発: pycache削除のみ"
	@echo "  make logs          - ログ表示 (follow)"
	@echo "  make ps            - 稼働中コンテナ一覧"
	@echo "  make config        - マージ後の compose 設定確認"
	@echo ""
	@echo "Prod:"
	@echo "  make prod-up       - 本番: 起動（compose本体のみ）"
	@echo "  make prod-down     - 本番: 停止（※volumesは保持）"
	@echo "  make prod-build    - 本番: ノーキャッシュビルド"
	@echo "  make prod-restart  - 本番: down -> build -> up"
	@echo "  make prod-rebuild  - 本番: 再作成（※volumes維持・データ保持）"
	@echo "  make prod-config   - 本番 compose 設定確認"

# -----------------------------------
# 開発用
# -----------------------------------
up:
	$(COMPOSE_DEV) up -d --remove-orphans

down:
	# 開発用: ボリュームまで削除（DB初期化）
	$(COMPOSE_DEV) down -v --remove-orphans

build:
	$(COMPOSE_DEV) build --no-cache

restart: down build up

# 開発: キャッシュ起因の不整合を排除 → 完全クリーン再構築
rebuild: clean-pycache
	$(COMPOSE_DEV) down -v --remove-orphans
	$(COMPOSE_DEV) build --no-cache
	$(COMPOSE_DEV) up -d --force-recreate --remove-orphans

logs:
	$(COMPOSE_DEV) logs -f

ps:
	$(COMPOSE_DEV) ps

config:
	$(COMPOSE_DEV) config

# __pycache__, *.pyc をホスト側から除去
clean-pycache:
	# Unix/WSL 推奨
	-find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	-find . -type f -name "*.py[co]" -delete 2>/dev/null || true
# Windows ネイティブで find が不安定なら下を使う:
#	python - << 'PY'
#import os, shutil
#for root, dirs, files in os.walk('.', topdown=False):
#    for d in list(dirs):
#        if d == '__pycache__':
#            shutil.rmtree(os.path.join(root, d), ignore_errors=True)
#    for f in files:
#        if f.endswith(('.pyc', '.pyo')):
#            try: os.remove(os.path.join(root, f))
#            except: pass
#PY

# pycache だけ掃除したい時
fresh: clean-pycache

# -----------------------------------
# 本番用（override 無効）
# -----------------------------------
prod-up:
	$(COMPOSE_PROD) up -d --remove-orphans

prod-down:
	# 本番: データ保持のため -v は付けない
	$(COMPOSE_PROD) down --remove-orphans

prod-build:
	$(COMPOSE_PROD) build --no-cache

prod-restart: prod-down prod-build prod-up

# 本番: 再作成（※ボリュームは維持）
prod-rebuild:
	$(COMPOSE_PROD) down --remove-orphans
	$(COMPOSE_PROD) build --no-cache
	$(COMPOSE_PROD) up -d --force-recreate --remove-orphans

prod-config:
	$(COMPOSE_PROD) config
