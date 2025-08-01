.PHONY: up down build restart logs ps prod-up prod-build prod-restart

# --- 開発用 ---
up:
	docker compose up -d --remove-orphans

down:
	docker compose down -v --remove-orphans

build:
	docker compose build --no-cache

restart: down build up

rebuild:
	docker compose down -v --remove-orphans
	docker compose build --no-cache
	docker compose up -d --force-recreate --remove-orphans

logs:
	docker compose logs -f

ps:
	docker compose ps

# --- 本番用（override無効） ---
prod-up:
	docker compose -f docker-compose.yml up -d --remove-orphans

prod-build:
	docker compose -f docker-compose.yml build --no-cache

prod-restart: prod-down prod-build prod-up

prod-down:
	docker compose -f docker-compose.yml down -v --remove-orphans
