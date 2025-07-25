.PHONY: up down build restart logs ps prod-up prod-build prod-restart

# --- 開発用 ---
up:
	docker compose up

down:
	docker compose down -v --remove-orphans

build:
	docker compose build --no-cache

restart: down build up

logs:
	docker compose logs -f

ps:
	docker compose ps

# --- 本番用（override無効） ---
prod-up:
	docker compose -f docker-compose.yml up

prod-build:
	docker compose -f docker-compose.yml build --no-cache

prod-restart: prod-down prod-build prod-up

prod-down:
	docker compose -f docker-compose.yml down -v --remove-orphans
