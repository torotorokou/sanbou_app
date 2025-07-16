# === 基本コマンド ===
.PHONY: up down build restart logs ps

# 開発用：すべてのサービスを起動（フォアグラウンド）
up:
	docker compose up

# 停止とボリューム・孤児削除（完全停止）
down:
	docker compose down -v --remove-orphans

# キャッシュなしで全サービスを再ビルド
build:
	docker compose build --no-cache

# フル再起動（最も安全）
restart: down build up

# ログをリアルタイムで確認
logs:
	docker compose logs -f

# コンテナ状態一覧
ps:
	docker compose ps
