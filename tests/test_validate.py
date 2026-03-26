"""Tests for the pb-spec validate command and validation helpers."""

from pathlib import Path

from click.testing import CliRunner

from pb_spec.cli import main
from pb_spec.validation.design import validate_design_file
from pb_spec.validation.features import collect_feature_scenarios
from pb_spec.validation.packets import validate_feedback_file
from pb_spec.validation.tasks import (
    find_orphan_scenarios,
    parse_task_blocks,
    validate_task_file,
)

FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "validate"

VALID_TRACEABLE_FULL_DESIGN = """# Example Design

## Executive Summary

Concrete summary.

## Source Inputs & Normalization

### 2.1 Source Materials

Original design notes.

### 2.2 Normalization Approach

Normalized into a requirement ledger.

### 2.3 Source Requirement Ledger

| Requirement ID | Source Summary | Type | Notes |
| :--- | :--- | :--- | :--- |
| `R1` | `Support successful login` | `Functional` | `Must remain user-visible` |

## Requirements & Goals

Concrete requirements.

## Requirements Coverage Matrix

| Requirement ID | Covered In Design | Scenario Coverage | Task Coverage | Status / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `R1` | `Detailed Design` | `auth.feature / User authenticates successfully` | `Task 1.1` | `Covered` |

## Architecture Overview

Concrete architecture overview.

## Existing Components to Reuse

No existing components identified for reuse.

## Detailed Design

Concrete design details.

## Verification & Testing Strategy

Concrete verification strategy.

## Implementation Plan

Concrete implementation plan.
"""


def test_validate_tasks_requires_requirement_coverage_field(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Add validator shell

> **Context:** Add the first validator entry point.
> **Verification:** Run the CLI help and verify the command is listed.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Scenario Coverage:** N/A for CLI shell registration
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Add the command module.
- [ ] **BDD Verification:** N/A for CLI shell registration
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert "Missing required task field in Task 1.1: Requirement Coverage" in errors


def test_validate_tasks_rejects_unknown_requirement_coverage_ids(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R2`
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Return token on valid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login.
- [ ] **BDD Verification:** Run auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file, known_requirement_ids={"R1"})

    assert errors == ["Unknown requirement reference in Task 1.1: R2"]


def test_parse_tasks_extracts_task_blocks_and_required_fields(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Add validator shell

> **Context:** Add the first validator entry point.
> **Verification:** Run the CLI help and verify the command is listed.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Scenario Coverage:** N/A for CLI shell registration
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Add the command module.
- [ ] **BDD Verification:** N/A for CLI shell registration
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    task_blocks = parse_task_blocks(tasks_file)

    assert len(task_blocks) == 1
    assert task_blocks[0].task_id == "Task 1.1"
    assert task_blocks[0].name == "Add validator shell"
    assert task_blocks[0].fields["Status"] == "🔴 TODO"
    assert task_blocks[0].fields["Loop Type"] == "TDD-only"
    assert task_blocks[0].fields["Scenario Coverage"] == "N/A for CLI shell registration"
    assert task_blocks[0].checkbox_lines == ["- [ ] **Step 1:** Add the command module."]


def test_validate_tasks_reports_missing_required_field(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Add validator shell

> **Context:** Add the first validator entry point.
> **Verification:** Run the CLI help and verify the command is listed.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A for CLI shell registration
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Add the command module.
- [ ] **BDD Verification:** N/A for CLI shell registration
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == ["Missing required task field in Task 1.1: Scenario Coverage"]


def test_validate_tasks_reports_missing_task_blocks(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

- [ ] Step 1: This file never defines a Task X.Y block.
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == ["No valid Task X.Y blocks found in tasks.md"]


def test_validate_tasks_accepts_legacy_todo_as_pending_input(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Normalize legacy status

> **Context:** Accept older pending task markers.
> **Verification:** Validate the task file.

- **Status:** TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A for compatibility input
- **Scenario Coverage:** N/A for compatibility input
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** N/A for compatibility input
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == []


def test_validate_tasks_rejects_invalid_status_value(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Reject unknown status

> **Context:** Do not allow arbitrary task states.
> **Verification:** Validate the task file.

- **Status:** COMPLETE-ish
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A for compatibility input
- **Scenario Coverage:** N/A for compatibility input
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** N/A for compatibility input
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == ["Invalid task status in Task 1.1: COMPLETE-ish"]


def test_validate_tasks_rejects_done_without_required_verification_entries(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Reject incomplete done task

> **Context:** Done tasks must not keep verification checkboxes open.
> **Verification:** Validate the task file.

- **Status:** 🟢 DONE
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A for compatibility input
- **Scenario Coverage:** N/A for compatibility input
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** N/A for compatibility input
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert len(errors) == 1
    assert "Task marked DONE still has incomplete verification evidence in Task 1.1" in errors[0]
    assert "BDD Verification" in errors[0]
    assert "Advanced Test Verification" in errors[0]
    assert "Runtime Verification" in errors[0]


def test_validate_tasks_accepts_done_with_unchecked_step(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Accept done with unchecked step

> **Context:** Done tasks need verification evidence checked, not step checkboxes.
> **Verification:** Validate the task file.

- **Status:** 🟢 DONE
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A for compatibility input
- **Scenario Coverage:** N/A for compatibility input
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [x] **BDD Verification:** N/A for compatibility input
- [x] **Advanced Test Verification:** N/A because no advanced tests apply
- [x] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == []


def test_validate_tasks_rejects_done_with_incomplete_verification_evidence(
    tmp_path: Path,
) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Reject done with unchecked verification

> **Context:** Done tasks must have all verification evidence checked.
> **Verification:** Validate the task file.

- **Status:** 🟢 DONE
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A for compatibility input
- **Scenario Coverage:** N/A for compatibility input
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [x] **Step 1:** Parse the task.
- [ ] **BDD Verification:** Run the auth scenario.
- [x] **Advanced Test Verification:** N/A because no advanced tests apply
- [x] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == [
        "Task marked DONE still has incomplete verification evidence in Task 1.1: BDD Verification"
    ]


def test_feature_inventory_extracts_scenarios_from_feature_files(tmp_path: Path) -> None:
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    feature_file = features_dir / "auth.feature"
    feature_file.write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted

  Scenario: User receives an auth error
    Given the user has invalid credentials
    When the user signs in
    Then an error is shown
""",
        encoding="utf-8",
    )

    scenario_inventory = collect_feature_scenarios(features_dir)

    assert scenario_inventory == {
        "User authenticates successfully": feature_file,
        "User receives an auth error": feature_file,
    }


def test_validate_reports_missing_scenario_reference(tmp_path: Path) -> None:
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Validate auth scenario mapping

> **Context:** Keep Scenario Coverage aligned with real feature files.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R1`
- **Scenario Coverage:** User receives an auth error
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** Run the auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    scenario_inventory = collect_feature_scenarios(features_dir)
    errors = validate_task_file(tasks_file, scenario_inventory=scenario_inventory)

    assert errors == ["Scenario reference not found for Task 1.1: User receives an auth error"]


def test_validate_rejects_noop_scenario_coverage_for_bdd_task(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Reject N/A scenario coverage for BDD task

> **Context:** BDD tasks must point to concrete scenarios.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R1`
- **Scenario Coverage:** N/A because this is not runtime-facing work
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** Run the auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == [
        "Scenario Coverage must name a concrete scenario for Task 1.1 when Loop Type is BDD+TDD"
    ]


def test_find_orphan_scenarios_detects_unreferenced_scenarios(tmp_path: Path) -> None:
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted

  Scenario: User receives an auth error
    Given the user has invalid credentials
    When the user signs in
    Then an error is shown
""",
        encoding="utf-8",
    )
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R1`
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Return token on valid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login.
- [ ] **BDD Verification:** Run auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    scenario_inventory = collect_feature_scenarios(features_dir)
    task_blocks = parse_task_blocks(tasks_file)
    orphans = find_orphan_scenarios(scenario_inventory, task_blocks)

    assert orphans == ["User receives an auth error"]


def test_find_orphan_scenarios_returns_empty_when_all_referenced(tmp_path: Path) -> None:
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R1`
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Return token on valid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login.
- [ ] **BDD Verification:** Run auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    scenario_inventory = collect_feature_scenarios(features_dir)
    task_blocks = parse_task_blocks(tasks_file)
    orphans = find_orphan_scenarios(scenario_inventory, task_blocks)

    assert orphans == []


def test_find_orphan_scenarios_ignores_na_task_coverage(tmp_path: Path) -> None:
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Internal refactor

> **Context:** Refactor internals.
> **Verification:** Run unit tests.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal scaffolding
- **Scenario Coverage:** N/A because this is internal scaffolding
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Refactor module.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    scenario_inventory = collect_feature_scenarios(features_dir)
    task_blocks = parse_task_blocks(tasks_file)
    orphans = find_orphan_scenarios(scenario_inventory, task_blocks)

    assert orphans == ["User authenticates successfully"]


def test_validate_command_rejects_unreferenced_scenarios(
    tmp_path: Path,
) -> None:
    spec_dir = tmp_path / "spec"
    features_dir = spec_dir / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted

  Scenario: User receives an auth error
    Given the user has invalid credentials
    When the user signs in
    Then an error is shown
""",
        encoding="utf-8",
    )
    (spec_dir / "design.md").write_text(VALID_TRACEABLE_FULL_DESIGN, encoding="utf-8")
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R1`
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Return token on valid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login.
- [ ] **BDD Verification:** Run auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(spec_dir)])

    assert result.exit_code != 0
    assert (
        "Orphan scenario not referenced by any task: User receives an auth error" in result.output
    )


def test_validate_reports_missing_context_quote_field(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Require quoted context

> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A because this is internal work
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == ["Missing required task field in Task 1.1: Context"]


def test_validate_reports_missing_behavioral_contract_field(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Require behavioral contract

> **Context:** Preserve compatibility while adding validation.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A because this is internal work
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == ["Missing required task field in Task 1.1: Behavioral Contract"]


def test_validate_reports_missing_checkbox_verification_entries(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Require verification checkboxes

> **Context:** Task closure needs explicit verification entries.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A because this is internal work
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == [
        "Missing required task field in Task 1.1: BDD Verification",
        "Missing required task field in Task 1.1: Advanced Test Verification",
        "Missing required task field in Task 1.1: Runtime Verification",
    ]


def test_validate_rejects_invalid_loop_type_value(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Reject invalid loop type

> **Context:** Loop type should be constrained to supported values.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** Manual-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A because this is internal work
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == ["Invalid loop type in Task 1.1: Manual-only"]


def test_validate_rejects_duplicate_task_ids(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: First task

> **Context:** First task context.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A because this is internal work
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the first task.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work

### Task 1.1: Duplicate task

> **Context:** Duplicate task context.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A because this is internal work
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the duplicate task.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == ["Duplicate task ID in tasks.md: Task 1.1"]


def test_validate_rejects_bare_na_scenario_coverage(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Require reason for scenario N/A

> **Context:** Internal work may use N/A, but it still needs a reason.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == ["N/A value must include a reason in Task 1.1: Scenario Coverage"]


def test_validate_rejects_bare_na_bdd_verification(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Require reason for BDD verification N/A

> **Context:** Internal work may skip BDD, but the reason must be explicit.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A because this is internal work
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** N/A
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == ["N/A value must include a reason in Task 1.1: BDD Verification"]


def test_validate_requires_advanced_test_coverage_when_verification_is_concrete(
    tmp_path: Path,
) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Add property tests

> **Context:** Broad input-domain logic needs property testing.
> **Verification:** Run property tests.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A because this is internal work
- **Behavioral Contract:** Correctness guaranteed by property tests
- **Simplification Focus:** N/A
- [ ] **Step 1:** Add property tests.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** uv run pytest tests/test_properties.py --hypothesis-show-statistics
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == [
        "Advanced Test Coverage is required when Advanced Test Verification is concrete in Task 1.1"
    ]


def test_validate_accepts_advanced_test_coverage_with_concrete_verification(
    tmp_path: Path,
) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Add property tests

> **Context:** Broad input-domain logic needs property testing.
> **Verification:** Run property tests.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A because this is internal work
- **Behavioral Contract:** Correctness guaranteed by property tests
- **Simplification Focus:** N/A
- **Advanced Test Coverage:** Property tests for parser input domain
- [ ] **Step 1:** Add property tests.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** uv run pytest tests/test_properties.py --hypothesis-show-statistics
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == []


def test_validate_skips_advanced_test_coverage_check_when_verification_is_na(
    tmp_path: Path,
) -> None:
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text(
        """# Example Tasks

### Task 1.1: Simple task

> **Context:** No advanced tests needed.
> **Verification:** Run unit tests.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Requirement Coverage:** N/A because this is internal work
- **Scenario Coverage:** N/A because this is internal work
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement feature.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    errors = validate_task_file(tasks_file)

    assert errors == []


def test_validate_design_accepts_full_mode_sections(tmp_path: Path) -> None:
    design_file = tmp_path / "design.md"
    design_file.write_text(VALID_TRACEABLE_FULL_DESIGN, encoding="utf-8")

    errors = validate_design_file(design_file)

    assert errors == []


def test_validate_design_requires_requirement_traceability_sections(tmp_path: Path) -> None:
    design_file = tmp_path / "design.md"
    design_file.write_text(
        """# Example Design

## Executive Summary

Concrete summary.

## Requirements & Goals

Concrete requirements.

## Architecture Overview

Concrete architecture overview.

## Existing Components to Reuse

No existing components identified for reuse.

## Detailed Design

Concrete design details.

## Verification & Testing Strategy

Concrete verification strategy.

## Implementation Plan

Concrete implementation plan.
""",
        encoding="utf-8",
    )

    errors = validate_design_file(design_file)

    assert "Missing required design section in design.md: Source Inputs & Normalization" in errors
    assert "Missing required design section in design.md: Requirements Coverage Matrix" in errors


def test_validate_design_rejects_unmapped_source_requirement_ids(tmp_path: Path) -> None:
    design_file = tmp_path / "design.md"
    design_file.write_text(
        """# Example Design

## Executive Summary

Concrete summary.

## Source Inputs & Normalization

### 2.1 Source Materials

Original design notes.

### 2.2 Normalization Approach

Normalized into a requirement ledger.

### 2.3 Source Requirement Ledger

| Requirement ID | Source Summary | Type | Notes |
| :--- | :--- | :--- | :--- |
| `R1` | `Support successful login` | `Functional` | `Must remain user-visible` |

## Requirements & Goals

Concrete requirements.

## Requirements Coverage Matrix

| Requirement ID | Covered In Design | Scenario Coverage | Task Coverage | Status / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `R2` | `Detailed Design` | `auth.feature / User authenticates successfully` | `Task 1.1` | `Covered` |

## Architecture Overview

Concrete architecture overview.

## Existing Components to Reuse

No existing components identified for reuse.

## Detailed Design

Concrete design details.

## Verification & Testing Strategy

Concrete verification strategy.

## Implementation Plan

Concrete implementation plan.
""",
        encoding="utf-8",
    )

    errors = validate_design_file(design_file)

    assert (
        "Requirement ID listed in Source Requirement Ledger but missing from Requirements Coverage Matrix: R1"
        in errors
    )
    assert (
        "Requirement ID listed in Requirements Coverage Matrix but missing from Source Requirement Ledger: R2"
        in errors
    )


def test_validate_command_rejects_unknown_matrix_scenario_reference(tmp_path: Path) -> None:
    spec_dir = tmp_path / "spec"
    features_dir = spec_dir / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )
    (spec_dir / "design.md").write_text(
        VALID_TRACEABLE_FULL_DESIGN.replace(
            "auth.feature / User authenticates successfully",
            "auth.feature / User receives an auth error",
        ),
        encoding="utf-8",
    )
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R1`
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Return token on valid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login.
- [ ] **BDD Verification:** Run auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(spec_dir)])

    assert result.exit_code != 0
    assert (
        "Scenario reference not found in Requirements Coverage Matrix for R1: User receives an auth error"
        in result.output
    )


def test_validate_command_rejects_unknown_matrix_task_reference(tmp_path: Path) -> None:
    spec_dir = tmp_path / "spec"
    features_dir = spec_dir / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )
    (spec_dir / "design.md").write_text(
        VALID_TRACEABLE_FULL_DESIGN.replace("Task 1.1", "Task 9.9"),
        encoding="utf-8",
    )
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R1`
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Return token on valid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login.
- [ ] **BDD Verification:** Run auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(spec_dir)])

    assert result.exit_code != 0
    assert (
        "Task reference not found in Requirements Coverage Matrix for R1: Task 9.9" in result.output
    )


def test_validate_command_rejects_matrix_task_without_requirement_alignment(
    tmp_path: Path,
) -> None:
    spec_dir = tmp_path / "spec"
    features_dir = spec_dir / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Scenario: User authenticates successfully
    Given the user has valid credentials
    When the user signs in
    Then access is granted
""",
        encoding="utf-8",
    )
    (spec_dir / "design.md").write_text(VALID_TRACEABLE_FULL_DESIGN, encoding="utf-8")
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Implement login

> **Context:** Add login endpoint.
> **Verification:** Run auth tests.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R2`
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Return token on valid credentials
- **Simplification Focus:** N/A
- [ ] **Step 1:** Implement login.
- [ ] **BDD Verification:** Run auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(spec_dir)])

    assert result.exit_code != 0
    assert (
        "Task reference does not cover requirement in Requirements Coverage Matrix for R1: Task 1.1"
        in result.output
    )


def test_validate_design_accepts_lightweight_mode_sections(tmp_path: Path) -> None:
    design_file = tmp_path / "design.md"
    design_file.write_text(
        """# Example Design

## Summary

Concrete summary.

## Approach

Concrete approach.

## Architecture Decisions

Concrete architecture decisions.

## BDD/TDD Strategy

Concrete BDD/TDD strategy.

## Code Simplification Constraints

Concrete code simplification constraints.

## BDD Scenario Inventory

Concrete scenario inventory.

## Existing Components to Reuse

No existing components identified for reuse.

## Verification

Concrete verification plan.
""",
        encoding="utf-8",
    )

    errors = validate_design_file(design_file)

    assert errors == []


def test_validate_design_reports_missing_required_section(tmp_path: Path) -> None:
    design_file = tmp_path / "design.md"
    design_file.write_text(
        VALID_TRACEABLE_FULL_DESIGN.replace(
            "## Detailed Design\n\nConcrete design details.\n\n",
            "",
        ),
        encoding="utf-8",
    )

    errors = validate_design_file(design_file)

    assert errors == ["Missing required design section in design.md: Detailed Design"]


def test_validate_design_rejects_placeholder_section_content(tmp_path: Path) -> None:
    design_file = tmp_path / "design.md"
    design_file.write_text(
        VALID_TRACEABLE_FULL_DESIGN.replace(
            "## Executive Summary\n\nConcrete summary.",
            "## Executive Summary\n\nTBD",
        ),
        encoding="utf-8",
    )

    errors = validate_design_file(design_file)

    assert errors == [
        "Required design section is empty or placeholder in design.md: Executive Summary"
    ]


def test_validate_design_requires_existing_components_section(tmp_path: Path) -> None:
    design_file = tmp_path / "design.md"
    design_file.write_text(
        VALID_TRACEABLE_FULL_DESIGN.replace(
            "## Existing Components to Reuse\n\nNo existing components identified for reuse.\n\n",
            "",
        ),
        encoding="utf-8",
    )

    errors = validate_design_file(design_file)

    assert errors == ["Missing required design section in design.md: Existing Components to Reuse"]


def test_validate_design_requires_bdd_scenario_inventory_when_strategy_present(
    tmp_path: Path,
) -> None:
    design_file = tmp_path / "design.md"
    design_file.write_text(
        """# Example Design

## Summary

Concrete summary.

## Approach

Concrete approach.

## Architecture Decisions

Concrete architecture decisions.

## BDD/TDD Strategy

- **BDD Runner:** behave
- **BDD Command:** uv run behave

## Code Simplification Constraints

Keep it simple.

## Existing Components to Reuse

No existing components identified for reuse.

## Verification

Concrete verification plan.
""",
        encoding="utf-8",
    )

    errors = validate_design_file(design_file)

    assert errors == ["Missing required design section in design.md: BDD Scenario Inventory"]


def test_validate_design_accepts_explicit_no_existing_components(tmp_path: Path) -> None:
    design_file = tmp_path / "design.md"
    design_file.write_text(VALID_TRACEABLE_FULL_DESIGN, encoding="utf-8")

    errors = validate_design_file(design_file)

    assert errors == []


def test_validate_feedback_accepts_complete_build_blocked_packet(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🛑 Build Blocked — Task 2.3: Stabilize validator

Reason: 3 consecutive failed attempts (initial + 2 retries)
Loop Type: BDD+TDD
Scenario Coverage: auth.feature + User authenticates successfully

What We Tried:
- Attempt 1: Added task parsing checks.
- Attempt 2: Adjusted feature mapping.

Failure Evidence:
- uv run pytest tests/test_validate.py -k packets -> \"AssertionError: missing section\"

Failing Step: Then the validate command should reject incomplete packets

Suggested Design Change:
- Update design.md to define packet parsing boundaries and adjust tasks.md to add packet validation work.

Impact:
- Task 2.3 and Task 2.4 need updated validation helpers.

Next Action:
- Run /pb-refine validate-packets and then retry /pb-build validate-packets.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert result.is_valid()
    assert result.to_error_strings() == []


def test_validate_feedback_reports_missing_build_blocked_sections(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🛑 Build Blocked — Task 2.3: Stabilize validator

Reason: 3 consecutive failed attempts (initial + 2 retries)
Loop Type: BDD+TDD
Scenario Coverage: auth.feature + User authenticates successfully

What We Tried:
- Attempt 1: Added task parsing checks.

Failing Step: Then the validate command should reject incomplete packets

Suggested Design Change:
- Update design.md to define packet parsing boundaries and adjust tasks.md to add packet validation work.

Impact:
- Task 2.3 and Task 2.4 need updated validation helpers.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Incomplete 🛑 Build Blocked packet. Missing required section(s): Failure Evidence, Next Action"
    ]


def test_validate_feedback_reports_missing_dcr_sections(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: auth.feature + User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.

Failure Evidence:
- uv run pytest tests/test_validate.py -k packets -> \"AssertionError: expected no errors\"

Impact:
- Task 2.4 must change before packet-aware refinement works.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Incomplete 🔄 Design Change Request packet. Missing required section(s): Failing Step, Suggested Change"
    ]


def test_validate_feedback_rejects_placeholder_required_packet_section(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: auth.feature + User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.

Failure Evidence: TBD
Failing Step: N/A
Suggested Change: Add structured packet parsing.
Suggested Change: Update design.md to define structured packet parsing.
Impact: Task 2.4 must change before packet-aware refinement works.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Required packet section is empty or placeholder in 🔄 Design Change Request: Failure Evidence"
    ]


def test_validate_feedback_rejects_generic_failure_evidence_summary(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🛑 Build Blocked — Task 2.3: Stabilize validator

Reason: 3 consecutive failed attempts (initial + 2 retries)
Loop Type: BDD+TDD
Scenario Coverage: auth.feature + User authenticates successfully

What We Tried:
- Attempt 1: Added task parsing checks.

Failure Evidence:
- The tests failed repeatedly during validation.

Failing Step: Then the validate command should reject incomplete packets

Suggested Design Change:
- Update design.md to define packet parsing boundaries and adjust tasks.md to add packet validation work.

Impact:
- Task 2.3 and Task 2.4 need updated validation helpers.

Next Action:
- Run /pb-refine validate-packets and then retry /pb-build validate-packets.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Failure Evidence must include concrete command output or quoted error text in 🛑 Build Blocked"
    ]


def test_validate_feedback_accepts_quoted_error_text_without_command(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: auth.feature + User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.

Failure Evidence:
- \"AssertionError: expected no errors\"

Failing Step: N/A
Suggested Change: Add structured packet parsing.
Suggested Change: Update design.md to define structured packet parsing.
Impact: Task 2.4 must change before packet-aware refinement works.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert result.is_valid()
    assert result.to_error_strings() == []


def test_validate_feedback_rejects_non_gherkin_failing_step(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🛑 Build Blocked — Task 2.3: Stabilize validator

Reason: 3 consecutive failed attempts (initial + 2 retries)
Loop Type: BDD+TDD
Scenario Coverage: auth.feature + User authenticates successfully

What We Tried:
- Attempt 1: Added task parsing checks.

Failure Evidence:
- uv run pytest tests/test_validate.py -k packets -> \"AssertionError: missing section\"

Failing Step: The validator failed after the scenario ran.

Suggested Design Change:
- Update design.md to define packet parsing boundaries and adjust tasks.md to add packet validation work.

Impact:
- Task 2.3 and Task 2.4 need updated validation helpers.

Next Action:
- Run /pb-refine validate-packets and then retry /pb-build validate-packets.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Failing Step must be a Gherkin step or N/A in 🛑 Build Blocked"
    ]


def test_validate_feedback_accepts_na_failing_step(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: auth.feature + User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.

Failure Evidence:
- \"AssertionError: expected no errors\"

Failing Step: N/A
Suggested Change: Update design.md to define structured packet parsing.
Impact: Task 2.4 must change before packet-aware refinement works.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert result.is_valid()
    assert result.to_error_strings() == []


def test_validate_feedback_rejects_generic_build_blocked_next_action(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🛑 Build Blocked — Task 2.3: Stabilize validator

Reason: 3 consecutive failed attempts (initial + 2 retries)
Loop Type: BDD+TDD
Scenario Coverage: auth.feature + User authenticates successfully

What We Tried:
- Attempt 1: Added task parsing checks.

Failure Evidence:
- uv run pytest tests/test_validate.py -k packets -> \"AssertionError: missing section\"

Failing Step: Then the validate command should reject incomplete packets

Suggested Design Change:
- Update design.md to define packet parsing boundaries and adjust tasks.md to add packet validation work.

Impact:
- Task 2.3 and Task 2.4 need updated validation helpers.

Next Action:
- Revisit the design and try again later.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Next Action must include concrete /pb-refine and /pb-build follow-up commands in 🛑 Build Blocked"
    ]


def test_validate_feedback_accepts_concrete_build_blocked_next_action(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🛑 Build Blocked — Task 2.3: Stabilize validator

Reason: 3 consecutive failed attempts (initial + 2 retries)
Loop Type: BDD+TDD
Scenario Coverage: auth.feature + User authenticates successfully

What We Tried:
- Attempt 1: Added task parsing checks.

Failure Evidence:
- uv run pytest tests/test_validate.py -k packets -> \"AssertionError: missing section\"

Failing Step: Then the validate command should reject incomplete packets

Suggested Design Change:
- Update design.md to define packet parsing boundaries and adjust tasks.md to add packet validation work.

Impact:
- Task 2.3 and Task 2.4 need updated validation helpers.

Next Action:
- Run /pb-refine validate-packets with this block, then re-run /pb-build validate-packets.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert result.is_valid()
    assert result.to_error_strings() == []


def test_validate_feedback_rejects_generic_suggested_design_change(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🛑 Build Blocked — Task 2.3: Stabilize validator

Reason: 3 consecutive failed attempts (initial + 2 retries)
Loop Type: BDD+TDD
Scenario Coverage: auth.feature + User authenticates successfully

What We Tried:
- Attempt 1: Added task parsing checks.

Failure Evidence:
- uv run pytest tests/test_validate.py -k packets -> \"AssertionError: missing section\"

Failing Step: Then the validate command should reject incomplete packets

Suggested Design Change:
- Simplify the approach and improve the implementation.

Impact:
- Task 2.3 and Task 2.4 need updated validation helpers.

Next Action:
- Run /pb-refine validate-packets with this block, then re-run /pb-build validate-packets.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Suggested Design Change must reference design.md or tasks.md in 🛑 Build Blocked"
    ]


def test_validate_feedback_rejects_generic_dcr_suggested_change(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: auth.feature + User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.

Failure Evidence:
- \"AssertionError: expected no errors\"

Failing Step: N/A
Suggested Change: Adjust the approach and make the structure clearer.
Impact: Task 2.4 must change before packet-aware refinement works.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Suggested Change must reference design.md in 🔄 Design Change Request"
    ]


def test_validate_feedback_accepts_artifact_targeted_suggested_changes(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🛑 Build Blocked — Task 2.3: Stabilize validator

Reason: 3 consecutive failed attempts (initial + 2 retries)
Loop Type: BDD+TDD
Scenario Coverage: auth.feature + User authenticates successfully

What We Tried:
- Attempt 1: Added task parsing checks.

Failure Evidence:
- uv run pytest tests/test_validate.py -k packets -> \"AssertionError: missing section\"

Failing Step: Then the validate command should reject incomplete packets

Suggested Design Change:
- Update design.md to define packet parsing boundaries and adjust tasks.md to add packet validation work.

Impact:
- Task 2.3 and Task 2.4 need updated validation helpers.

Next Action:
- Run /pb-refine validate-packets with this block, then re-run /pb-build validate-packets.

🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: auth.feature + User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.

Failure Evidence:
- \"AssertionError: expected no errors\"

Failing Step: N/A
Suggested Change: Update design.md to define structured packet parsing expectations.
Impact: Task 2.4 must change before packet-aware refinement works.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert result.is_valid()
    assert result.to_error_strings() == []


def test_validate_feedback_rejects_generic_build_blocked_impact(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🛑 Build Blocked — Task 2.3: Stabilize validator

Reason: 3 consecutive failed attempts (initial + 2 retries)
Loop Type: BDD+TDD
Scenario Coverage: auth.feature + User authenticates successfully

What We Tried:
- Attempt 1: Added task parsing checks.

Failure Evidence:
- uv run pytest tests/test_validate.py -k packets -> \"AssertionError: missing section\"

Failing Step: Then the validate command should reject incomplete packets

Suggested Design Change:
- Update design.md to define packet parsing boundaries and adjust tasks.md to add packet validation work.

Impact:
- Validation behavior is affected and follow-up work is required.

Next Action:
- Run /pb-refine validate-packets with this block, then re-run /pb-build validate-packets.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Impact must reference affected tasks or explicitly say no other tasks are affected in 🛑 Build Blocked"
    ]


def test_validate_feedback_rejects_generic_dcr_impact(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: auth.feature + User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.

Failure Evidence:
- \"AssertionError: expected no errors\"

Failing Step: N/A
Suggested Change: Update design.md to define structured packet parsing.
Impact: This refinement has broader downstream consequences.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Impact must reference affected tasks or explicitly say no other tasks are affected in 🔄 Design Change Request"
    ]


def test_validate_feedback_accepts_explicit_no_other_tasks_impact(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: auth.feature + User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.

Failure Evidence:
- \"AssertionError: expected no errors\"

Failing Step: N/A
Suggested Change: Update design.md to define structured packet parsing.
Impact: No other tasks are affected beyond Task 2.4.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert result.is_valid()
    assert result.to_error_strings() == []


def test_validate_feedback_rejects_generic_build_blocked_scenario_coverage(
    tmp_path: Path,
) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🛑 Build Blocked — Task 2.3: Stabilize validator

Reason: 3 consecutive failed attempts (initial + 2 retries)
Loop Type: BDD+TDD
Scenario Coverage: User authenticates successfully

What We Tried:
- Attempt 1: Added task parsing checks.

Failure Evidence:
- uv run pytest tests/test_validate.py -k packets -> \"AssertionError: missing section\"

Failing Step: Then the validate command should reject incomplete packets

Suggested Design Change:
- Update design.md to define packet parsing boundaries and adjust tasks.md to add packet validation work.

Impact:
- Task 2.3 and Task 2.4 need updated validation helpers.

Next Action:
- Run /pb-refine validate-packets with this block, then re-run /pb-build validate-packets.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Scenario Coverage must reference a .feature file and scenario name in 🛑 Build Blocked"
    ]


def test_validate_feedback_rejects_generic_dcr_scenario_coverage(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.

Failure Evidence:
- \"AssertionError: expected no errors\"

Failing Step: N/A
Suggested Change: Update design.md to define structured packet parsing.
Impact: No other tasks are affected beyond Task 2.4.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert not result.is_valid()
    assert [e.message for e in result.errors] == [
        "Scenario Coverage must reference a .feature file and scenario name in 🔄 Design Change Request"
    ]


def test_validate_feedback_accepts_feature_file_and_scenario_name(tmp_path: Path) -> None:
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: auth.feature + User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.

Failure Evidence:
- \"AssertionError: expected no errors\"

Failing Step: N/A
Suggested Change: Update design.md to define structured packet parsing.
Impact: No other tasks are affected beyond Task 2.4.
""",
        encoding="utf-8",
    )

    result = validate_feedback_file(feedback_file)

    assert result.is_valid()
    assert result.to_error_strings() == []


# --- Generated-artifact build eligibility tests ---


def test_canonical_full_spec_is_build_eligible() -> None:
    """The canonical full-mode spec fixture must pass all validation checks."""
    spec_dir = FIXTURES_ROOT / "full_spec"
    if not spec_dir.is_dir():
        return

    errors: list[str] = []
    errors.extend(validate_design_file(spec_dir / "design.md"))

    scenario_inventory = collect_feature_scenarios(spec_dir / "features")
    errors.extend(validate_task_file(spec_dir / "tasks.md", scenario_inventory=scenario_inventory))

    assert errors == [], f"Canonical full spec has validation errors: {errors}"


def test_canonical_lightweight_spec_is_build_eligible() -> None:
    """The canonical lightweight spec fixture must pass all validation checks."""
    spec_dir = FIXTURES_ROOT / "lightweight_spec"
    if not spec_dir.is_dir():
        return

    errors: list[str] = []
    errors.extend(validate_design_file(spec_dir / "design.md"))

    scenario_inventory = collect_feature_scenarios(spec_dir / "features")
    errors.extend(validate_task_file(spec_dir / "tasks.md", scenario_inventory=scenario_inventory))

    assert errors == [], f"Canonical lightweight spec has validation errors: {errors}"


def test_canonical_full_spec_cli_validate_passes() -> None:
    """pb-spec validate must succeed for the canonical full-mode spec fixture."""
    spec_dir = FIXTURES_ROOT / "full_spec"
    if not spec_dir.is_dir():
        return

    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(spec_dir)])
    assert result.exit_code == 0, f"CLI validate failed: {result.output}"


def test_canonical_lightweight_spec_cli_validate_passes() -> None:
    """pb-spec validate must succeed for the canonical lightweight spec fixture."""
    spec_dir = FIXTURES_ROOT / "lightweight_spec"
    if not spec_dir.is_dir():
        return

    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(spec_dir)])
    assert result.exit_code == 0, f"CLI validate failed: {result.output}"


def test_canonical_medium_spec_is_build_eligible() -> None:
    """The canonical medium-complexity spec fixture must pass all validation checks."""
    spec_dir = FIXTURES_ROOT / "medium_spec"
    if not spec_dir.is_dir():
        return

    errors: list[str] = []
    errors.extend(validate_design_file(spec_dir / "design.md"))

    scenario_inventory = collect_feature_scenarios(spec_dir / "features")
    errors.extend(validate_task_file(spec_dir / "tasks.md", scenario_inventory=scenario_inventory))

    assert errors == [], f"Canonical medium spec has validation errors: {errors}"


def test_canonical_medium_spec_cli_validate_passes() -> None:
    """pb-spec validate must succeed for the canonical medium-complexity spec fixture."""
    spec_dir = FIXTURES_ROOT / "medium_spec"
    if not spec_dir.is_dir():
        return

    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(spec_dir)])
    assert result.exit_code == 0, f"CLI validate failed: {result.output}"
