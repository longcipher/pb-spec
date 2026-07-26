# pb-spec Agent Rules

## Stack

- Python 3.14+, `uv` for all commands (`uv run`, `uv add`, `uv sync --all-groups`)
- Runtime dep: `click`. Dev deps: `ruff`, `ty`, `pytest`, `behave`.
- Never edit `pyproject.toml` versions by hand — use `uv add`.
- CLI output via `click.echo` (see `src/pb_spec/output.py`); no `print()`.

## Quality Gates

```bash
just format && just lint && just test && just bdd && just test-all
```

- `ruff check` + `ruff format` — zero errors.
- `ty check` — zero errors.
- `pytest` — all pass.
- `behave` — all scenarios pass.
- Type annotations required on all public functions. Use `from __future__ import annotations`, `X | None` syntax.

## Conventions

- Match existing code style in `src/pb_spec/`. Comment density and naming follow what's already there.
- `dataclasses(frozen=True)` for value types (see `validation/result.py`).
- Regex-based markdown parsing (see `validation/parser.py`).
- Read-only validation: the tool never modifies source files.
- Errors via structured `ValidationError` + `ValidationResult` types, not bare exceptions.
- One logical change per commit. English only in docs/comments/commits.

## Workflow

- BDD outside-in: Gherkin in `features/` → `pytest` inner loop → implementation.
- Step definitions thin; reuse domain modules from `src/pb_spec/`.
- Tests under `tests/` mirroring source structure. BDD under `features/`.
- Fix root cause, never suppress warnings or patch symptoms.

## Git

- Never use `git worktree`. Work directly on the current branch.
- Never commit/push unless explicitly asked.
- Never force push to main/master.

## SDD Artifacts

Spec-driven workflow lives in `specs/<spec-dir>/`:

- `features/*.feature` — source of truth (Gherkin)
- `design.md` — 5 required + optional sections
- `tasks.md` — 4-field blocks (Context / Verification / Status / Scenario Coverage)

See `docs/contract.md` for the executable type contract.
