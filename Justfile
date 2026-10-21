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
    uvx rumdl fmt .

# Lint code with ruff
lint:
    uv run ruff check .
    uvx rumdl check .

# Lint and auto-fix issues
lint-fix:
    uv run ruff check . --fix

# Run type checker
type-check:
    uv run ty check src tests

# Run format, lint, and type-check
check: format lint type-check

# Run tests (strict TDD suite, single process)
test:
    uv run pytest

# Run tests in parallel with pytest-xdist (fast feedback)
test-fast:
    uv run pytest -n auto

# Run property-based tests (hypothesis) only
test-prop:
    uv run pytest -m property

# Run tests with coverage (coverage gate: fail_under = 80)
coverage:
    uv run pytest --cov=pb_spec --cov-report=term-missing

# Run incremental mutation testing on changed files (vs main/master)
mutation:
    ./scripts/run-mutation-diff.sh

# Run mutation testing against HEAD (staged + unstaged changes)
mutation-head:
    ./scripts/run-mutation-diff.sh --against HEAD

# Run a clean, full mutation pass (wipes mutmut cache — CI-grade strictness)
mutation-full:
    rm -rf mutants .mutmut-cache
    ./scripts/run-mutation-diff.sh --against HEAD

# Run all checks and tests
all: check coverage

# CI checks (format, lint, type-check, coverage, mutation gate).
# The mutation script exits 2 when there are no changed files to test; on a
# clean checkout that is a skip, not a failure.
ci:
    uv run ruff format --check .
    uv run ruff check .
    uvx rumdl check .
    uv run ty check src tests
    uv run pytest --cov=pb_spec --cov-report=term-missing
    @bash -c './scripts/run-mutation-diff.sh || [ $? -eq 2 ]'

# Full verification gate: strict TDD tests + coverage + incremental mutation
verify: coverage mutation

# Run skill-up evals for a skill (opencode engine). e.g. `just skill-eval pb-plan`
skill-eval skill:
    skill-up run skills/{{skill}}/evals/eval.yaml

# Validate all skill eval configs
skill-eval-validate:
    for s in skills/*/evals/eval.yaml skills/*/evals/eval-cmd.yaml; do skill-up validate "$s"; done

# Build and publish to PyPI
publish:
    uv build
    uv publish
