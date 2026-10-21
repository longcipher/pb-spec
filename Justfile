# Default recipe to display help
default:
  @just --list

# Sync all dependency groups into the project environment
sync:
  uv sync --all-groups

# Alias kept for compatibility with the old install-dev recipe
install-dev: sync

# Format Python code and markdown
format:
  uv run ruff format .
  uvx rumdl fmt .

# Auto-fix lint findings that formatting cannot resolve
fix:
  uv run ruff check . --fix
  uvx rumdl check --fix .

# Alias kept for compatibility with the old lint-fix recipe
lint-fix: fix

# Run every lint gate: ruff, markdown, and type checks
lint:
  uv run ruff check .
  uvx rumdl check .
  uv run ty check src tests

# Type check the package and the test suite
typecheck:
  uv run ty check src tests

# Alias kept for compatibility with the old type-check recipe
type-check: typecheck

# Run format, lint, and type check
check: format lint type-check

# Run the strict TDD pytest suite
test:
  uv run pytest

# Run the pytest suite in parallel with xdist
test-fast:
  uv run pytest -n auto

# Run only the Hypothesis property tests
test-prop:
  uv run pytest -m property

# Run the test suite with the coverage gate (fail_under = 80)
test-coverage:
  uv run pytest --cov=pb_spec --cov-report=term-missing

# Alias kept for compatibility with the old coverage recipe
coverage: test-coverage

# Run incremental mutation testing on files changed against main/master
mutation:
  ./scripts/run-mutation-diff.sh

# Run incremental mutation testing against HEAD (staged + unstaged changes)
mutation-head:
  ./scripts/run-mutation-diff.sh --against HEAD

# Run a clean, full mutation pass (wipes the mutmut cache)
mutation-full:
  rm -rf mutants .mutmut-cache
  ./scripts/run-mutation-diff.sh --against HEAD

# Run the coverage gate and the incremental mutation gate
verify: test-coverage mutation

# Run every check plus the coverage report
all: check coverage

# Run the CI gate: format check, lint, coverage, and the incremental mutation gate
ci:
  uv run ruff format --check .
  uv run ruff check .
  uvx rumdl check .
  uv run ty check src tests
  uv run pytest --cov=pb_spec --cov-report=term-missing
  @bash -c './scripts/run-mutation-diff.sh || [ $? -eq 2 ]'

# Build the sdist and wheel
build:
  uv build

# Fail if Chinese characters appear anywhere in the tracked tree
check-cn:
  @ if rg --line-number --column "\p{Han}" .; then echo "Chinese characters found"; exit 1; fi

# Remove build artifacts and tool caches (keeps the mutmut cache; use just mutation-full to reset it)
clean:
  rm -rf dist/ .pytest_cache/ .ruff_cache/ .rumdl_cache/ .hypothesis/ htmlcov/ .coverage
  find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
  find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Install the dev dependencies (rumdl is fetched on demand by uvx)
setup:
  uv sync --all-groups

# Refresh the dependency lock file
lock:
  uv lock

# Upgrade every locked dependency
update:
  uv lock --upgrade

# Validate every skill eval config
skill-eval-validate:
  for s in skills/*/evals/eval.yaml skills/*/evals/eval-cmd.yaml; do skill-up validate "$s"; done

# Run the skill evals for one skill (e.g. just skill-eval pb-plan)
skill-eval skill:
  skill-up run skills/{{skill}}/evals/eval.yaml

# Build and publish to PyPI (requires RELEASE_CONFIRM=1)
publish:
  @test -n "$$RELEASE_CONFIRM" || { echo "Set RELEASE_CONFIRM=1 to publish to PyPI"; exit 1; }
  uv build
  uv publish
