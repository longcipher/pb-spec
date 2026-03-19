# pb-spec Validate Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal `pb-spec validate <spec-dir>` command that statically validates the current markdown workflow contract without changing the existing artifact family or command surface semantics.

**Architecture:** Keep the current Click CLI structure intact and add a narrow validation layer under `src/pb_spec/` for `tasks.md` parsing, task state validation, feature scenario inventory, and scenario-reference checks. Start with the smallest validator tranche defined in [docs/contract.md](../contract.md), and keep the implementation dependency-free and stdlib-first.

**Tech Stack:** Python 3.12, Click, pathlib, regex via stdlib `re`, pytest, existing pb-spec CLI layout

---

## File Structure

### New Files

- `src/pb_spec/commands/validate.py`
  Purpose: Click command entry point for `pb-spec validate`.
- `src/pb_spec/validation/__init__.py`
  Purpose: Export validator-facing types and top-level validation entry points.
- `src/pb_spec/validation/tasks.py`
  Purpose: Parse `tasks.md` into typed task blocks and validate required fields and task states.
- `src/pb_spec/validation/features.py`
  Purpose: Inventory `.feature` files and extract scenario names for reference validation.
- `tests/test_validate.py`
  Purpose: Focused command- and parser-level tests for the new validation surface.

### Modified Files

- `src/pb_spec/cli.py`
  Purpose: Register the new `validate` command.
- `tests/test_cli.py`
  Purpose: Assert help output and basic CLI registration for `validate`.
- `README.md`
  Purpose: Document the new validation command after the implementation is stable.

### Optional Test Fixtures

If inline string fixtures become unwieldy, create:

- `tests/fixtures/validate/valid_spec/...`
- `tests/fixtures/validate/missing_task_field/...`
- `tests/fixtures/validate/bad_state_transition/...`
- `tests/fixtures/validate/missing_scenario_reference/...`

Do not create fixture directories unless the inline setup becomes too noisy.

---

## Task 1: Add CLI coverage and register the `validate` command shell

**Files:**

- Create: `src/pb_spec/commands/validate.py`
- Modify: `src/pb_spec/cli.py`
- Modify: `tests/test_cli.py`
- Test: `tests/test_cli.py`
- [ ] **Step 1: Write the failing CLI tests**

Add tests that assert:

```python
def test_help_contains_validate_subcommand():
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.output


def test_validate_help_contains_spec_dir_argument():
    result = runner.invoke(main, ["validate", "--help"])
    assert result.exit_code == 0
    assert "SPEC_DIR" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py -k "validate" -v`
Expected: FAIL because the CLI does not yet expose a `validate` command.

- [ ] **Step 3: Write minimal CLI implementation**

Create `src/pb_spec/commands/validate.py` with a Click command skeleton:

```python
@click.command("validate")
@click.argument("spec_dir", type=click.Path(path_type=Path))
def validate_cmd(spec_dir: Path) -> None:
    raise click.ClickException("not implemented")
```

Then register it in `src/pb_spec/cli.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli.py -k "validate" -v`
Expected: PASS because the command now exists and is wired into the CLI.

- [ ] **Step 5: Commit**

```bash
git add src/pb_spec/commands/validate.py src/pb_spec/cli.py tests/test_cli.py
git commit -m "feat(cli): add validate command shell"
```

## Task 2: Add failing task parser tests for required task fields

**Files:**

- Create: `src/pb_spec/validation/__init__.py`
- Create: `src/pb_spec/validation/tasks.py`
- Create: `tests/test_validate.py`
- Test: `tests/test_validate.py`
- [ ] **Step 1: Write the failing parser tests**

Add parser-focused tests for:

```python
def test_parse_tasks_extracts_task_blocks_and_required_fields(tmp_path):
    # write a minimal tasks.md with one valid Task 1.1 block
    # assert one parsed block with the expected task id and field map


def test_validate_tasks_reports_missing_required_field(tmp_path):
    # omit Scenario Coverage or Runtime Verification
    # assert a validation error naming the missing field and task id
```

For this first slice, required-field assertions must follow [docs/contract.md](../contract.md) but may be introduced in two passes:

- initial pass in this task: `Status`, `Loop Type`, `Scenario Coverage`, and step checkboxes
- follow-on pass in the same module before command completion: `Context`, `Verification`, `BDD Verification`, `Advanced Test Verification`, and `Runtime Verification`

The command should not ship with only the smaller subset validated, but the implementation work may layer the checks progressively across Tasks 2 through 5.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_validate.py -k "task" -v`
Expected: FAIL because no validation package or task parser exists yet.

- [ ] **Step 3: Write minimal implementation**

Implement in `src/pb_spec/validation/tasks.py`:

- a small typed task representation
- regex-based task block splitting by `### Task X.Y:`
- required field extraction
- required field validation

Keep scope intentionally narrow:

- no markdown AST
- no design.md parsing yet
- no blocked-build or DCR block parsing yet
- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_validate.py -k "task" -v`
Expected: PASS with precise missing-field diagnostics.

- [ ] **Step 5: Commit**

```bash
git add src/pb_spec/validation/__init__.py src/pb_spec/validation/tasks.py tests/test_validate.py docs/contract.md
git commit -m "feat(validate): parse task blocks and required fields"
```

## Task 3: Add failing task state transition validation tests

**Files:**

- Modify: `src/pb_spec/validation/tasks.py`
- Modify: `tests/test_validate.py`
- Test: `tests/test_validate.py`
- [ ] **Step 1: Write the failing state validation tests**

Add tests for:

```python
def test_validate_tasks_accepts_legacy_todo_as_pending_input(tmp_path):
    ...


def test_validate_tasks_rejects_invalid_status_value(tmp_path):
    ...


def test_validate_tasks_rejects_done_without_required_verification_entries(tmp_path):
    ...


def test_validate_tasks_rejects_done_reached_directly_from_todo(tmp_path):
  ...
```

The validator only needs to inspect markdown content, not actual test execution output.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_validate.py -k "status or state" -v`
Expected: FAIL because state validation rules are not yet implemented.

- [ ] **Step 3: Write minimal implementation**

Extend `tasks.py` to validate:

- allowed statuses
- legacy `TODO` compatibility
- `🟢 DONE` does not coexist with obviously incomplete verification checkboxes in the same block

Do not overreach into full execution-evidence semantics yet. Stay text-structural.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_validate.py -k "status or state" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pb_spec/validation/tasks.py tests/test_validate.py
git commit -m "feat(validate): enforce task state rules"
```

## Task 4: Add failing feature inventory and scenario reference tests

**Files:**

- Create: `src/pb_spec/validation/features.py`
- Modify: `src/pb_spec/validation/__init__.py`
- Modify: `tests/test_validate.py`
- Test: `tests/test_validate.py`
- [ ] **Step 1: Write the failing feature tests**

Add tests for:

```python
def test_feature_inventory_extracts_scenarios_from_feature_files(tmp_path):
    ...


def test_validate_reports_missing_scenario_reference(tmp_path):
    ...


def test_validate_rejects_noop_scenario_coverage_for_bdd_task(tmp_path):
  ...
```

The happy path should include one task block with `Scenario Coverage` referencing a real `Scenario` in a `.feature` file.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_validate.py -k "feature or scenario" -v`
Expected: FAIL because feature inventory and scenario-reference validation do not yet exist.

- [ ] **Step 3: Write minimal implementation**

Implement in `features.py`:

- `.feature` file discovery under `<spec-dir>/features`
- simple `Scenario:` line extraction
- scenario inventory map

Then wire task validation to check that concrete `Scenario Coverage` references resolve.

For this first slice:

- allow `N/A` with reason only for task blocks whose `Loop Type` is `TDD-only`
- reject `Scenario Coverage: N/A ...` for task blocks whose `Loop Type` is `BDD+TDD`
- do not yet parse `Feature:` titles or tags
- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_validate.py -k "feature or scenario" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pb_spec/validation/features.py src/pb_spec/validation/__init__.py tests/test_validate.py
git commit -m "feat(validate): inventory feature scenarios"
```

## Task 5: Add failing end-to-end command tests and implement command diagnostics

**Files:**

- Modify: `src/pb_spec/commands/validate.py`
- Modify: `tests/test_validate.py`
- Test: `tests/test_validate.py`
- [ ] **Step 1: Write the failing command tests**

Add command-level tests for:

```python
def test_validate_command_reports_success_for_valid_spec(tmp_path):
    ...


def test_validate_command_reports_named_failure_for_invalid_spec(tmp_path):
    ...


def test_validate_command_rejects_missing_spec_dir(tmp_path):
    ...
```

Prefer precise, user-readable diagnostics such as:

- `Missing required task field in Task 1.1: Scenario Coverage`
- `Scenario reference not found for Task 1.1: User authenticates successfully`
- `No .feature files found under ...`
- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_validate.py -k "validate_command" -v`
Expected: FAIL because the command still raises `not implemented`.

- [ ] **Step 3: Write minimal implementation**

Implement `validate_cmd` so it:

- resolves the given spec directory
- validates the presence of `tasks.md` and `features/`
- runs the task and feature validators
- prints a success message on valid input
- raises `click.ClickException` on invalid input

Keep this version intentionally narrow:

- no `design.md` validation yet
- no blocked-build or DCR block parsing yet
- no JSON output mode yet
- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_validate.py -k "validate_command" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pb_spec/commands/validate.py tests/test_validate.py
git commit -m "feat(validate): add end-to-end spec validation command"
```

## Task 6: Document the command and run focused project verification

**Files:**

- Modify: `README.md`
- Modify: `tests/test_cli.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_validate.py`
- [ ] **Step 1: Write the failing docs/help test**

If needed, add a focused regression test that the CLI help still includes all subcommands, including `validate`.

- [ ] **Step 2: Run test to verify it fails or stays pending**

Run: `uv run pytest tests/test_cli.py -k "help_contains" -v`
Expected: FAIL only if the help output has not yet been updated by prior steps.

- [ ] **Step 3: Write minimal documentation updates**

Document in `README.md`:

- the `pb-spec validate <spec-dir>` command
- its initial scope limits
- the fact that it validates the existing markdown contract rather than introducing a new spec file
- [ ] **Step 4: Run focused verification**

Run: `uv run pytest tests/test_cli.py tests/test_validate.py -v`
Expected: PASS

Run: `uv run ruff check src/pb_spec tests`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_cli.py tests/test_validate.py
git commit -m "docs(validate): document minimal validation command"
```

---

## Execution Notes

- Keep the implementation stdlib-only unless a parser dependency becomes unavoidable.
- Do not implement `design.md` parsing in this first slice.
- Do not implement blocked-build or DCR block validation in this first slice.
- Do not add JSON output, SARIF, or CI integration yet.
- Prefer explicit diagnostics over generic "invalid spec" failures.

## Definition of Done

- [ ] `pb-spec validate <spec-dir>` exists and is registered in the CLI.
- [ ] Valid specs return success.
- [ ] Invalid specs return precise diagnostics.
- [ ] Task block parsing covers required fields.
- [ ] Allowed status values and minimal state checks are enforced.
- [ ] `.feature` scenario inventory exists.
- [ ] `Scenario Coverage` references can be checked against real scenarios.
- [ ] README documents the new command and its initial scope.
