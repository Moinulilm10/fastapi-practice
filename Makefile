.PHONY: up down restart logs build print-urls

up:
	docker compose up --build -d
	@$(MAKE) --no-print-directory print-urls

down:
	docker compose down

restart:
	docker compose down
	docker compose up --build -d
	@$(MAKE) --no-print-directory print-urls

print-urls:
	@printf '\nFastAPI:    http://localhost:8000\nStreamlit:  http://localhost:8501\npgAdmin:    http://localhost:5050\nPostgreSQL: localhost:5432\n'

logs:
	docker compose logs -f api db pgadmin frontend

build:
	docker compose build