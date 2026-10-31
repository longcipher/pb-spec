# pb-spec Agent Instructions

## Non-negotiables

- Surgical edits only: every changed line must trace to the request. No drive-by refactors, no reformatting untouched code, no deleting pre-existing dead code (mention it instead).
- Fix root causes. Never silence a warning, weaken a check, or patch a symptom to make a gate pass.
- Never report completion while any `just` gate below fails. Report the failure verbatim and stop.
- Stop and ask when a request is ambiguous, conflicts with existing conventions, or requires credentials, publishing, or destructive operations.
- When a correction reveals a missing rule, add one specific rule here ("always X for Y", never "be careful with Y"); delete rules that never catch real errors.

## Scope

- `pb-spec` ships the Agent Skills workflow packages (`pb-plan`, `pb-build`, `pb-refine`, `pb-improve`, `pb-goal`) and the `pb-spec` CLI that validates their artifacts and gates the TDD loop.
- `src/pb_spec/` is the package: `cli.py`, `commands/` (`validate`, `test`, `mutate`, `verify`, `report`, `discovery`), `validation/` (markdown parser, plan/scanner/build checks, rumdl bridge, `contract_sections.toml`), `config.py`, `exceptions.py`, `output.py`, `git_utils.py`.
- `skills/<skill>/` holds each `SKILL.md` plus its `evals/` (`eval.yaml`, `eval-cmd.yaml`, `cases/*.yaml`, `fixtures/`); `skills/*-workspace/` is generated eval output and is gitignored. The chain is `/pb-plan` -> `/pb-build`, with `/pb-refine` for spec iteration, `/pb-improve` for read-only audits, and `/pb-goal` for goal-driven runs.
- `scripts/run-mutation-diff.sh` is an optional reference implementation for this repo; the authoritative mutation policy for skill users lives in `skills/pb-build/SKILL.md` and uses native Rust/Python/Node commands. `docs/contract.md` plus `src/pb_spec/validation/contract_sections.toml` are the executable type contract.
- The artifact contract is fixed: `design.md` must carry the five required sections (Summary, Approach, Architecture Decisions, TDD & Mutation Testing Strategy, Verification) and each `tasks.md` block must carry Context, Verification, Status, and Test Coverage. An optional `Mutation: <src-glob>[, <src-glob>]` field marks the only tasks that participate in mutation testing; absent means mutation-exempt.
- English only in code, comments, docs, and commit messages.

## Execution

- Parallelize aggressively: dispatch subagents for independent research, exploration, and implementation. Independent spec tasks may fan out; two tasks that touch the same file never share a wave.
- NEVER use `git worktree`. Edit the current branch in place.
- Never commit or push unless explicitly asked, and never force push to `main`/`master`.
- Strict TDD for behavior changes: failing `pytest` test first (example and Hypothesis property tests), smallest change to pass, then a scope-bounded mutation pass only when the spec task declares `Mutation:` targets.
- Decision protocol: pick the best option and record it as an assumption; ask the user — and wait — only for genuinely incomparable, expensive-to-undo choices.

## Verification loop

After each feature or bug fix, in order; any failure means the task is not done:

```bash
just format
just lint
just test
just mutation   # spec-marked; exits 0 without running when no task declares Mutation:
```

`just lint` runs `ruff check`, `uvx rumdl check` and `ty check src tests`; `just ci` adds the `ruff format --check` gate and runs no mutation. `just mutation` runs only when the latest `specs/*/tasks.md` declares `Mutation: <src-glob>` targets and the changed files match them; it scores the kill rate against an 85% threshold. It hard-fails (exit 3) when the scope exceeds 3 files, 60 mutants, or 300 seconds. Never run whole-repo mutation, never invoke bare `mutmut run` / `cargo mutants`, and never add a `mutation-full` recipe.

## uv rules

- Never hand-edit dependency versions in `pyproject.toml`. Runtime deps: `uv add <package>`; dev deps: `uv add --group dev <package>`.
- Always execute code through `uv run`; commit `uv.lock`; install everything with `uv sync --all-groups`.
- Build backend is `uv_build` (`uv build`). Console entry point: `pb-spec`.
- Python 3.14+ (`ruff` targets py314; `ty` is pinned to 3.14). Ruff config lives in `pyproject.toml` under `[tool.ruff]` — there is no `ruff.toml`.

## Dependency choices

- Runtime dependency is `click` and nothing else; dev dependencies are `hypothesis`, `mutmut`, `pytest`, `pytest-cov`, `pytest-xdist`, `ruff`, `ty`.
- TOML: stdlib `tomllib` (`validation/plan.py`); markdown: `re` plus the regex helpers in `validation/parser.py` and `validation/scanner.py` — do not pull in a markdown library.
- External tools are invoked, not vendored: `rumdl` through `uvx`, `mutmut` and `pytest` through `uv run`, `skill-up` for skill evals (`just skill-eval <skill>`, `just skill-eval-validate`).
- Forbidden: `print()` (use `click.echo` via `src/pb_spec/output.py`), `pandas`, `requests`, `aiohttp`, and any new runtime dependency without an explicit reason.

## Code conventions

- `from __future__ import annotations` in every module; full type annotations on all public functions; `X | None`, never `Optional[X]`.
- Value types are `@dataclass(frozen=True)` (`validation/result.py`); structured failures are `ValidationError` + `ValidationResult`, not bare exceptions. The exception hierarchy lives in `exceptions.py` (`SpecNotFoundError`, `FileReadError`).
- Validation is strictly read-only: never modify the files being validated.
- Match the existing style in `src/pb_spec/` — comment density and naming follow what is already there.
- Tests live under `tests/` as flat `test_*.py` modules named after the source module they cover; property tests carry `pytestmark = pytest.mark.property` and run in the normal suite (`just test-prop` selects them). Use fixtures, `pytest.raises`, and `pytest.approx` — never `setUp`/`tearDown`.
- Coverage gate is `fail_under = 80`; `just test-coverage` must stay above it.
