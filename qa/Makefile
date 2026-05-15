.PHONY: type lint test

type:
	uv run ty check

lint:
	uv run ruff check

test:
	uv run pytest --cov=qa
# 	uv run pytest --cov=qa --cov-report=term --cov-fail-under=80 tests
