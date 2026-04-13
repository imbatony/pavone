.PHONY: install test lint format type-check check ci

install:
	uv sync

test:
	uv run pytest

lint:
	uv run flake8 pavone/ tests/

format:
	uv run black pavone/ tests/
	uv run isort pavone/ tests/

type-check:
	uv run pyright

check: format lint type-check test

ci: check
