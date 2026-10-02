.PHONY: up down test lint seed-demo eval e2e models

up:
	docker compose up --build -d

down:
	docker compose down -v

test:
	pytest backend/tests

lint:
	python -m flake8 backend/app || true

seed-demo:
	python scripts/seed_users.py

eval:
	python scripts/eval.py

e2e:
	cd web && npm run e2e || true

models:
	python scripts/download_models.py
