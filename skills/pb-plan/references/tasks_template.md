# tasks.md — Implementation Tasks

Test-driven task list produced by `/pb-plan`. Each task is the smallest unit
that carries its own test cycle and earns an independent reviewer's gate. Tasks
are ordered as a DAG — respect dependencies, no forward references.

## Task Block Template

### Task X.Y — <task name>

- Context: <why this task exists, what to do, key files, dependencies on prior tasks>
- Verification: <exact command(s) + expected output that proves this task is done>
- Status: 🔴 TODO
- Test Coverage: <pytest test paths proving this task, or `N/A` for infrastructure-only tasks>

Status transitions: `🔴 TODO` → `🟡 IN PROGRESS` → `🟢 DONE`. Exceptional states:
`⏭️ SKIPPED`, `🔄 DCR`, `⛔ OBSOLETE`.

## Example

### Task 1.1 — Configure test toolchain

- Context: Project has no parallel/property/mutation tooling yet. Add `pytest-xdist`,
  `hypothesis`, `pytest-cov`, and `mutmut` to dev dependencies so the strict TDD +
  mutation loop is runnable. No dependencies.
- Verification: `uv run pytest -n auto -q` exits 0; `uv run mutmut --help` works.
- Status: 🔴 TODO
- Test Coverage: N/A

### Task 2.1 — Successful login with valid credentials

- Context: Implement the happy path for login. Depends on Task 1.1. Write failing tests
  in `tests/auth/test_login.py` (including a `hypothesis` property test on credential
  validation) before implementing `src/auth/login.py`.
- Verification: `uv run pytest tests/auth/test_login.py -q` passes; `./scripts/run-mutation-diff.sh` exits 0 with score ≥ 85%.
- Status: 🔴 TODO
- Test Coverage: tests/auth/test_login.py::test_login_success, tests/auth/test_login.py::test_credentials_property

### Task 2.2 — Reject login with unknown user

- Context: Implement the error path for unknown users. Depends on Task 2.1 producing
  the login entry point. Reuse the same fixture pattern.
- Verification: `uv run pytest tests/auth/test_login.py -q` passes; `./scripts/run-mutation-diff.sh` exits 0 with score ≥ 85%.
- Status: 🔴 TODO
- Test Coverage: tests/auth/test_login.py::test_login_unknown_user
