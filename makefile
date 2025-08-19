.PHONY: help \
        up down build restart rebuild logs ps clean-pycache fresh config \
        prod-up prod-down prod-build prod-restart prod-rebuild prod-config \
        bootstrap rotate-keys

# -----------------------------------
# 設定
# -----------------------------------
COMPOSE_DEV  = docker compose               # 開発（override 自動適用）
COMPOSE_PROD = docker compose -f docker-compose.yml  # 本番（override 無効）

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
	@echo "  make config        - マージ後の compose 設定確認（※ローカル専用）"
	@echo ""
	@echo "Prod:"
	@echo "  make prod-up       - 本番: 起動（compose本体のみ）"
	@echo "  make prod-down     - 本番: 停止（※volumesは保持）"
	@echo "  make prod-build    - 本番: ノーキャッシュビルド"
	@echo "  make prod-restart  - 本番: down -> build -> up"
	@echo "  make prod-rebuild  - 本番: 再作成（※volumes維持・データ保持）"
	@echo "  make prod-config   - 本番 compose 設定確認（※ローカルでの事前確認向け）"
	@echo ""
	@echo "Setup/Security:"
	@echo "  make bootstrap     - .env と envs/.env.* の雛形を作成"
	@echo "  make rotate-keys   - OpenAI/Gemini のAPIキーを安全に差し替え（入力非表示）"

# -----------------------------------
# 開発用
# -----------------------------------
up:
	$(COMPOSE_DEV) up -d --remove-orphans

down:
	# 開発: ボリュームまで削除（DB初期化）
	$(COMPOSE_DEV) down -v --remove-orphans

build:
	$(COMPOSE_DEV) build --no-cache

restart: down build up

# 開発: キャッシュ起因の不整合を排除 → 完全クリーン再構築
rebuild: clean-pycache
	$(COMPOSE_DEV) down --remove-orphans     # ← -v を外す（volume保持）
	$(COMPOSE_DEV) build --no-cache
	$(COMPOSE_DEV) up -d --force-recreate --remove-orphans

logs:
	$(COMPOSE_DEV) logs -f

ps:
	$(COMPOSE_DEV) ps

# ---- 重要：configはローカル専用（CIでは失敗させる） ----
config:
	@[ -z "$$CI" ] || (echo "CI環境では 'make config' を禁止しています。ローカルで実行してください。" ; exit 1)
	$(COMPOSE_DEV) config

# __pycache__, *.pyc をホスト側から除去
clean-pycache:
	# Unix/WSL 推奨
	-find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	-find . -type f -name "*.py[co]" -delete 2>/dev/null || true
# Windows ネイティブで find が不安定なら、必要に応じて Python ワンライナーに切替可

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
	@[ -z "$$CI" ] || (echo "CI環境では 'make prod-config' を禁止しています。ローカルで実行してください。" ; exit 1)
	$(COMPOSE_PROD) config

# -----------------------------------
# 初期化・セキュリティ
# -----------------------------------

# 必要ファイルをまとめて作成（空でもOK）
bootstrap:
	@mkdir -p envs
	@[ -f .env ] || { \
	  echo "POSTGRES_USER=myuser"        > .env; \
	  echo "POSTGRES_PASSWORD=mypassword" >> .env; \
	  echo "POSTGRES_DB=myapp"            >> .env; \
	  echo "POSTGRES_HOST=db"             >> .env; \
	  echo "POSTGRES_PORT=5432"           >> .env; \
	  echo "PYTHONPATH=/backend"          >> .env; \
	  echo "created .env"; }
	@for f in ai_api ledger_api sql_api rag_api; do \
	  [ -f envs/.env.$$f ] || { : > envs/.env.$$f; echo "created envs/.env.$$f"; }; \
	done

# APIキーを安全に差し替え（入力は非表示 / .bakにバックアップ作成）
# - envs/.env.ai_api と envs/.env.rag_api を対象（必要なら下のリストにサービス追加）
rotate-keys:
	@mkdir -p envs
	@for f in envs/.env.ai_api envs/.env.rag_api; do \
	  [ -f $$f ] || { : > $$f; echo "created $$f"; }; \
	done ; \
	echo "Enter NEW OPENAI_API_KEY (input hidden). Leave empty to skip:" ; \
	read -s OPENAI_KEY ; echo ; \
	if [ -n "$$OPENAI_KEY" ]; then \
	  for f in envs/.env.ai_api envs/.env.rag_api ; do \
	    if grep -q '^OPENAI_API_KEY=' $$f 2>/dev/null ; then \
	      sed -i.bak "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=$$OPENAI_KEY/" $$f ; \
	    else \
	      echo "OPENAI_API_KEY=$$OPENAI_KEY" >> $$f ; \
	    fi ; \
	    echo "updated OPENAI_API_KEY -> $$f (backup: $$f.bak)" ; \
	  done ; \
	fi ; \
	echo "Enter NEW GEMINI_API_KEY (input hidden). Leave empty to skip:" ; \
	read -s GEMINI_KEY ; echo ; \
	if [ -n "$$GEMINI_KEY" ]; then \
	  for f in envs/.env.ai_api envs/.env.rag_api ; do \
	    if grep -q '^GEMINI_API_KEY=' $$f 2>/dev/null ; then \
	      sed -i.bak "s/^GEMINI_API_KEY=.*/GEMINI_API_KEY=$$GEMINI_KEY/" $$f ; \
	    else \
	      echo "GEMINI_API_KEY=$$GEMINI_KEY" >> $$f ; \
	    fi ; \
	    echo "updated GEMINI_API_KEY -> $$f (backup: $$f.bak)" ; \
	  done ; \
	fi ; \
	echo "Done. ※キーはGitにコミットしないでください（.env.example のみ共有）"
