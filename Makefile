.PHONY: up down restart logs build

up:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose down
	docker compose up --build -d

logs:
	docker compose logs -f api db

build:
	docker compose build