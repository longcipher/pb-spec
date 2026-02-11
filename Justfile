# Justfile for pb-spec project

# Default recipe to run when just is called without arguments
default:
    @just --list

# Install development dependencies
install-dev:
    uv sync --group dev

# Format code with ruff
format:
    uv run ruff format .

# Lint code with ruff
lint:
    uv run ruff check .

# Lint and auto-fix issues
lint-fix:
    uv run ruff check . --fix

# Run type checker
type-check:
    uv run ty check

# Run format, lint, and type-check
check: format lint type-check

# Run tests
test:
    uv run pytest

# Run all checks and tests
all: format lint type-check test

# CI checks (format, lint, type-check, test - for CI pipeline)
ci:
    uv run ruff format --check .
    uv run ruff check .
    uv run ty check
    uv run pytest

# Build and publish to PyPI
publish:
    uv build
    uv publish
