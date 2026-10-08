.PHONY: up down logs migrate rebuild

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f app

migrate:
	docker compose run --rm app alembic upgrade head

rebuild:
	docker compose up -d --build --force-recreate
