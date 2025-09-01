.PHONY: run dev docker-up docker-build fmt

run:
	uvicorn app.main:app --reload --port 8000

docker-build:
	docker build -t ai-email-assistant:latest .

docker-up:
	docker compose up --build

fmt:
	python -m black app || true
