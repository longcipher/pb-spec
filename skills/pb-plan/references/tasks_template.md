# tasks.md — Implementation Tasks

Scenario-driven task list produced by `/pb-plan`. Each task is the smallest unit
that carries its own test cycle and earns an independent reviewer's gate. Tasks
are ordered as a DAG — respect dependencies, no forward references.

## Task Block Template

### Task X.Y — <task name>

- Context: <why this task exists, what to do, key files, dependencies on prior tasks>
- Verification: <exact command(s) + expected output that proves this task is done>
- Status: 🔴 TODO
- Scenario Coverage: <@scenario-id list from .feature files, or `N/A` for non-BDD tasks>

Status transitions: `🔴 TODO` → `🟡 IN PROGRESS` → `🟢 DONE`. Exceptional states:
`⏭️ SKIPPED`, `🔄 DCR`, `⛔ OBSOLETE`.

## Example

### Task 1.1 — Configure BDD runner

- Context: Project has no `features/` discovery yet. Add behave config so `uv run behave features/ --dry-run` exits 0. No dependencies.
- Verification: `uv run behave specs/<spec-dir>/features/ --dry-run` exits 0 with no undefined steps.
- Status: 🔴 TODO
- Scenario Coverage: N/A

### Task 2.1 — Successful login with valid credentials

- Context: Implement the happy path for `@login-success`. Depends on Task 1.1. Add step definitions under `features/steps/login_steps.py` and minimal auth logic in `src/auth/login.py`.
- Verification: `uv run behave specs/<spec-dir>/features/login.feature --tags=@login-success` exits 0; `uv run pytest tests/auth/test_login.py -q` passes.
- Status: 🔴 TODO
- Scenario Coverage: @login-success

### Task 2.2 — Reject login with unknown user

- Context: Implement the error path for `@login-unknown-user`. Depends on Task 2.1 producing the login entry point. Reuse the same step definitions.
- Verification: `uv run behave specs/<spec-dir>/features/login.feature --tags=@login-unknown-user` exits 0.
- Status: 🔴 TODO
- Scenario Coverage: @login-unknown-user
