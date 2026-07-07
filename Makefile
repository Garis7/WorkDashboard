.PHONY: setup format lint typecheck test test-cov check-all run migrate

setup:
	uv sync
	uv run pre-commit install

format:
	uv run ruff format src tests

lint:
	uv run ruff check src tests --fix

typecheck:
	@echo "typecheck: skipped (no mypy configured yet)"

test:
	uv run pytest

test-cov:
	uv run pytest --cov=work_dashboard --cov-report=term-missing

check-all: format lint test

run:
	uv run uvicorn work_dashboard.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	uv run alembic upgrade head

migration:
	uv run alembic revision --autogenerate -m "$(MSG)"
