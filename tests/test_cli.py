"""Tests for pb-spec CLI entry point and basic commands."""

import subprocess
import tomllib
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from pb_spec import __version__ as package_version
from pb_spec.cli import main

runner = CliRunner()


VALID_FULL_DESIGN = """# Example Design

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


def get_project_version() -> str:
    """Read version from pyproject.toml."""
    root_dir = Path(__file__).parents[1]
    with open(root_dir / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def test_help_contains_subcommands():
    """pb-spec --help should list init, version, and update subcommands."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "validate" in result.output
    assert "version" in result.output
    assert "update" in result.output


def test_init_help_contains_global_option():
    """pb-spec init --help should show the global install option."""
    result = runner.invoke(main, ["init", "--help"])
    assert result.exit_code == 0
    assert "-g, --global" in result.output


def test_validate_help_contains_target_argument():
    """pb-spec validate --help should describe the validation target argument."""
    result = runner.invoke(main, ["validate", "--help"])
    assert result.exit_code == 0
    assert "TARGET" in result.output


def test_validate_succeeds_for_minimal_valid_spec(tmp_path: Path) -> None:
    """pb-spec validate should succeed for a spec dir with valid tasks and features."""
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
    (spec_dir / "design.md").write_text(VALID_FULL_DESIGN, encoding="utf-8")
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Validate auth scenario mapping

> **Context:** Keep Scenario Coverage aligned with real feature files.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Requirement Coverage:** `R1`
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** Run the auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    result = runner.invoke(main, ["validate", str(spec_dir)])

    assert result.exit_code == 0
    assert "Validation passed" in result.output


def test_validate_succeeds_for_complete_feedback_packet_file(tmp_path: Path) -> None:
    """pb-spec validate should succeed for a complete feedback packet markdown file."""
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
- Run /pb-refine validate-packets and then retry /pb-build validate-packets.
""",
        encoding="utf-8",
    )

    result = runner.invoke(main, ["validate", str(feedback_file)])

    assert result.exit_code == 0
    assert "Validation passed" in result.output


def test_validate_reports_invalid_feedback_packet_file(tmp_path: Path) -> None:
    """pb-spec validate should fail for an incomplete feedback packet markdown file."""
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """🔄 Design Change Request — Task 2.4: Refine validator flow

Scenario Coverage: auth.feature + User authenticates successfully

Problem: The packet parser cannot distinguish packet bodies from plain prose.
What We Tried: Added a regex without multiline capture.
Impact: Task 2.4 must change before packet-aware refinement works.
""",
        encoding="utf-8",
    )

    result = runner.invoke(main, ["validate", str(feedback_file)])

    assert result.exit_code != 0
    assert "Validation failed" in result.output
    assert "Incomplete 🔄 Design Change Request packet" in result.output


def test_validate_reports_feedback_file_without_packets(tmp_path: Path) -> None:
    """pb-spec validate should fail for a markdown file that does not contain any feedback packets."""
    feedback_file = tmp_path / "feedback.md"
    feedback_file.write_text(
        """# Notes

This file contains discussion, but no build-block or DCR packet.
""",
        encoding="utf-8",
    )

    result = runner.invoke(main, ["validate", str(feedback_file)])

    assert result.exit_code != 0
    assert "No 🛑 Build Blocked or 🔄 Design Change Request packets found in" in result.output


def test_validate_reports_missing_tasks_file(tmp_path: Path) -> None:
    """pb-spec validate should fail when tasks.md is missing."""
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
    (spec_dir / "design.md").write_text(VALID_FULL_DESIGN, encoding="utf-8")

    result = runner.invoke(main, ["validate", str(spec_dir)])

    assert result.exit_code != 0
    assert "Missing required file" in result.output
    assert "tasks.md" in result.output


def test_validate_reports_missing_design_file(tmp_path: Path) -> None:
    """pb-spec validate should fail when design.md is missing."""
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
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Validate auth scenario mapping

> **Context:** Keep Scenario Coverage aligned with real feature files.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Scenario Coverage:** User authenticates successfully
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** Run the auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    result = runner.invoke(main, ["validate", str(spec_dir)])

    assert result.exit_code != 0
    assert "Missing required file" in result.output
    assert "design.md" in result.output


def test_validate_reports_missing_feature_files(tmp_path: Path) -> None:
    """pb-spec validate should fail when the features directory has no .feature files."""
    spec_dir = tmp_path / "spec"
    (spec_dir / "features").mkdir(parents=True)
    (spec_dir / "design.md").write_text(VALID_FULL_DESIGN, encoding="utf-8")
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Validate auth scenario mapping

> **Context:** Keep Scenario Coverage aligned with real feature files.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Scenario Coverage:** N/A because this is internal scaffolding
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    result = runner.invoke(main, ["validate", str(spec_dir)])

    assert result.exit_code != 0
    assert "No .feature files found under" in result.output


def test_validate_reports_missing_feature_scenarios(tmp_path: Path) -> None:
    """pb-spec validate should fail when feature files contain no Scenario entries."""
    spec_dir = tmp_path / "spec"
    features_dir = spec_dir / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "auth.feature").write_text(
        """Feature: Authentication

  Background:
    Given auth is configured
""",
        encoding="utf-8",
    )
    (spec_dir / "design.md").write_text(VALID_FULL_DESIGN, encoding="utf-8")
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Validate auth scenario mapping

> **Context:** Keep Scenario Coverage aligned with real feature files.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** TDD-only
- **Scenario Coverage:** N/A because this is internal scaffolding
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** N/A because this task does not expose user-visible behavior
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    result = runner.invoke(main, ["validate", str(spec_dir)])

    assert result.exit_code != 0
    assert "No Scenario entries found under" in result.output


def test_validate_reports_validation_errors(tmp_path: Path) -> None:
    """pb-spec validate should print validation findings for invalid specs."""
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
    (spec_dir / "design.md").write_text(VALID_FULL_DESIGN, encoding="utf-8")
    (spec_dir / "tasks.md").write_text(
        """# Example Tasks

### Task 1.1: Validate auth scenario mapping

> **Context:** Keep Scenario Coverage aligned with real feature files.
> **Verification:** Validate the task file.

- **Status:** 🔴 TODO
- **Loop Type:** BDD+TDD
- **Scenario Coverage:** Unknown scenario
- **Behavioral Contract:** Preserve existing behavior
- **Simplification Focus:** N/A
- [ ] **Step 1:** Parse the task.
- [ ] **BDD Verification:** Run the auth scenario.
- [ ] **Advanced Test Verification:** N/A because no advanced tests apply
- [ ] **Runtime Verification:** N/A because this is not runtime-facing work
""",
        encoding="utf-8",
    )

    result = runner.invoke(main, ["validate", str(spec_dir)])

    assert result.exit_code != 0
    assert "Validation failed" in result.output
    assert "Scenario reference not found for Task 1.1: Unknown scenario" in result.output


def test_version_shows_version_number():
    """pb-spec version should print the version number."""
    expected_version = get_project_version()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert expected_version in result.output


def test_version_option():
    """pb-spec --version should print the version number."""
    expected_version = get_project_version()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert expected_version in result.output


def test_update_calls_uv():
    """pb-spec update should call uv tool upgrade pb-spec."""
    with patch("pb_spec.commands.update.subprocess.run") as mock_run:
        result = runner.invoke(main, ["update"])
        assert result.exit_code == 0
        mock_run.assert_called_once_with(["uv", "tool", "upgrade", "pb-spec"], check=True)


def test_update_missing_uv_returns_error_exit_code():
    """pb-spec update should fail with non-zero exit code when uv is missing."""
    with patch("pb_spec.commands.update.subprocess.run", side_effect=FileNotFoundError):
        result = runner.invoke(main, ["update"])
        assert result.exit_code != 0
        assert "uv is not installed" in result.output


def test_update_subprocess_error_returns_error_exit_code():
    """pb-spec update should fail with non-zero exit code when uv upgrade fails."""
    error = subprocess.CalledProcessError(2, ["uv", "tool", "upgrade", "pb-spec"])
    with patch("pb_spec.commands.update.subprocess.run", side_effect=error):
        result = runner.invoke(main, ["update"])
        assert result.exit_code != 0
        assert "exited with code 2" in result.output


def test_dunder_version_matches_project_version():
    """pb_spec.__version__ should match pyproject.toml project.version."""
    assert package_version == get_project_version()


def test_status_shows_task_statuses(tmp_path: Path):
    """status command shows task statuses."""
    # Create a minimal spec with tasks
    spec_dir = tmp_path / "specs" / "test-feature"
    spec_dir.mkdir(parents=True)

    (spec_dir / "design.md").write_text(
        "# Summary\nTest design\n## Architecture Decisions\nTest decisions\n## Verification\nTest verification\n"
    )

    (spec_dir / "tasks.md").write_text(
        "# Test Tasks\n\n### Task 1.1: Test Task\n"
        "> **Context:** Test context\n"
        "- **Status:** 🟢 DONE\n"
        "- **Loop Type:** TDD-only\n"
        "- **Requirement Coverage:** REQ-1\n"
        "- **Scenario Coverage:** N/A\n"
        "- **Behavioral Contract:** Test contract\n"
        "- **Simplification Focus:** Test focus\n"
        "- **Verification:** Test verification\n"
        "- **BDD Verification:** N/A\n"
        "- **Advanced Test Verification:** N/A\n"
        "- **Runtime Verification:** N/A\n"
        "- [x] **Step 1:** Test step\n"
    )

    features_dir = spec_dir / "features"
    features_dir.mkdir()
    (features_dir / "test.feature").write_text(
        "Feature: Test\n  Scenario: Test scenario\n    Given test\n"
    )

    result = subprocess.run(
        ["uv", "run", "pb-spec", "status", str(spec_dir)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "📊 Task Status" in result.stdout
    assert "Task 1.1: Test Task" in result.stdout
    assert "🟢 DONE" in result.stdout


def test_sync_dry_run_shows_changes(tmp_path: Path):
    """sync --dry-run shows what would be changed."""
    # Create a spec with mismatched status
    spec_dir = tmp_path / "specs" / "test-feature"
    spec_dir.mkdir(parents=True)

    (spec_dir / "design.md").write_text(
        "# Summary\nTest design\n## Architecture Decisions\nTest decisions\n## Verification\nTest verification\n"
    )

    (spec_dir / "tasks.md").write_text(
        "# Test Tasks\n\n### Task 1.1: Test Task\n"
        "> **Context:** Test context\n"
        "- **Status:** 🔴 TODO\n"
        "- **Loop Type:** TDD-only\n"
        "- **Requirement Coverage:** REQ-1\n"
        "- **Scenario Coverage:** N/A\n"
        "- **Behavioral Contract:** Test contract\n"
        "- **Simplification Focus:** Test focus\n"
        "- **Verification:** Test verification\n"
        "- **BDD Verification:** N/A\n"
        "- **Advanced Test Verification:** N/A\n"
        "- **Runtime Verification:** N/A\n"
        "- [x] **Step 1:** Test step\n"
    )

    features_dir = spec_dir / "features"
    features_dir.mkdir()
    (features_dir / "test.feature").write_text(
        "Feature: Test\n  Scenario: Test scenario\n    Given test\n"
    )

    result = subprocess.run(
        ["uv", "run", "pb-spec", "sync", str(spec_dir), "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "🔍 Dry Run" in result.stdout
    assert "🔴 TODO -> 🟢 DONE" in result.stdout


def test_sync_fixes_mismatched_status(tmp_path: Path):
    """sync command fixes mismatched task status."""
    # Create a spec with mismatched status
    spec_dir = tmp_path / "specs" / "test-feature"
    spec_dir.mkdir(parents=True)

    (spec_dir / "design.md").write_text(
        "# Summary\nTest design\n## Architecture Decisions\nTest decisions\n## Verification\nTest verification\n"
    )

    tasks_file = spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Test Tasks\n\n### Task 1.1: Test Task\n"
        "> **Context:** Test context\n"
        "- **Status:** 🔴 TODO\n"
        "- **Loop Type:** TDD-only\n"
        "- **Requirement Coverage:** REQ-1\n"
        "- **Scenario Coverage:** N/A\n"
        "- **Behavioral Contract:** Test contract\n"
        "- **Simplification Focus:** Test focus\n"
        "- **Verification:** Test verification\n"
        "- **BDD Verification:** N/A\n"
        "- **Advanced Test Verification:** N/A\n"
        "- **Runtime Verification:** N/A\n"
        "- [x] **Step 1:** Test step\n"
    )

    features_dir = spec_dir / "features"
    features_dir.mkdir()
    (features_dir / "test.feature").write_text(
        "Feature: Test\n  Scenario: Test scenario\n    Given test\n"
    )

    result = subprocess.run(
        ["uv", "run", "pb-spec", "sync", str(spec_dir)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "🔧" in result.stdout
    assert "🔴 TODO -> 🟢 DONE" in result.stdout

    # Verify the file was actually updated
    content = tasks_file.read_text()
    assert "- **Status:** 🟢 DONE" in content


def test_status_with_feature_name(tmp_path: Path):
    """status command supports feature name resolution."""
    # Create a spec with date-prefixed directory
    spec_dir = tmp_path / "specs" / "2026-03-09-01-test-feature"
    spec_dir.mkdir(parents=True)

    (spec_dir / "design.md").write_text(
        "# Summary\nTest design\n## Architecture Decisions\nTest decisions\n## Verification\nTest verification\n"
    )

    (spec_dir / "tasks.md").write_text(
        "# Test Tasks\n\n### Task 1.1: Test Task\n"
        "> **Context:** Test context\n"
        "- **Status:** 🟢 DONE\n"
        "- **Loop Type:** TDD-only\n"
        "- **Requirement Coverage:** REQ-1\n"
        "- **Scenario Coverage:** N/A\n"
        "- **Behavioral Contract:** Test contract\n"
        "- **Simplification Focus:** Test focus\n"
        "- **Verification:** Test verification\n"
        "- **BDD Verification:** N/A\n"
        "- **Advanced Test Verification:** N/A\n"
        "- **Runtime Verification:** N/A\n"
        "- [x] **Step 1:** Test step\n"
    )

    features_dir = spec_dir / "features"
    features_dir.mkdir()
    (features_dir / "test.feature").write_text(
        "Feature: Test\n  Scenario: Test scenario\n    Given test\n"
    )

    # Change to tmp_path directory so specs/ is found
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = subprocess.run(
            ["uv", "run", "pb-spec", "status", "test-feature"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "📊 Task Status" in result.stdout
        assert "Task 1.1: Test Task" in result.stdout
    finally:
        os.chdir(original_cwd)


def test_sync_with_feature_name(tmp_path: Path):
    """sync command supports feature name resolution."""
    # Create a spec with date-prefixed directory
    spec_dir = tmp_path / "specs" / "2026-03-09-01-test-feature"
    spec_dir.mkdir(parents=True)

    (spec_dir / "design.md").write_text(
        "# Summary\nTest design\n## Architecture Decisions\nTest decisions\n## Verification\nTest verification\n"
    )

    tasks_file = spec_dir / "tasks.md"
    tasks_file.write_text(
        "# Test Tasks\n\n### Task 1.1: Test Task\n"
        "> **Context:** Test context\n"
        "- **Status:** 🔴 TODO\n"
        "- **Loop Type:** TDD-only\n"
        "- **Requirement Coverage:** REQ-1\n"
        "- **Scenario Coverage:** N/A\n"
        "- **Behavioral Contract:** Test contract\n"
        "- **Simplification Focus:** Test focus\n"
        "- **Verification:** Test verification\n"
        "- **BDD Verification:** N/A\n"
        "- **Advanced Test Verification:** N/A\n"
        "- **Runtime Verification:** N/A\n"
        "- [x] **Step 1:** Test step\n"
    )

    features_dir = spec_dir / "features"
    features_dir.mkdir()
    (features_dir / "test.feature").write_text(
        "Feature: Test\n  Scenario: Test scenario\n    Given test\n"
    )

    # Change to tmp_path directory so specs/ is found
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = subprocess.run(
            ["uv", "run", "pb-spec", "sync", "test-feature"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "🔧" in result.stdout
        assert "🔴 TODO -> 🟢 DONE" in result.stdout

        # Verify the file was actually updated
        content = tasks_file.read_text()
        assert "- **Status:** 🟢 DONE" in content
    finally:
        os.chdir(original_cwd)
