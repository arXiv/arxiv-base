.PHONY: type lint format test

type:
	uv run ty check

lint:
	uv run ruff check

format:
	uv run ruff format

test:
	uv run pytest --cov=qa
# 	uv run pytest --cov=qa --cov-report=term --cov-fail-under=80 tests
