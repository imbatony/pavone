.PHONY: install test test-all test-cov format format-check lint type-check check ci clean build

install:
	uv sync

test:
	uv run pytest tests/ -v -m "not integration" --tb=short

test-all:
	uv run pytest tests/ -v --tb=short

test-cov:
	uv run pytest tests/ -v -m "not integration" --cov=pavone --cov-report=html --cov-report=term-missing

format:
	uv run black pavone/ tests/
	uv run isort pavone/ tests/

format-check:
	uv run black --check --diff pavone/ tests/
	uv run isort --check-only --diff pavone/ tests/

lint:
	uv run flake8 pavone/ tests/ --select=E9,F63,F7,F82
	uv run flake8 pavone/ tests/ --exit-zero

type-check:
	uv run pyright pavone/

check: format-check lint type-check test

ci: check

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml .pytest_cache

build:
	uv build
