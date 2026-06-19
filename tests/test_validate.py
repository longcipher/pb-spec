"""Unit tests for the validate command."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from pb_spec.cli import main
from pb_spec.commands.discovery import get_latest_spec_dir
from pb_spec.exceptions import SpecNotFoundError
from pb_spec.validation.build import validate_build, validate_task
from pb_spec.validation.plan import validate_plan, validate_tasks_structure


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


def _create_spec_files(
    spec_dir: Path,
    design_content: str | None = None,
    tasks_content: str | None = None,
    features_content: str | None = None,
) -> None:
    """Helper to create spec files."""
    spec_dir.mkdir(parents=True, exist_ok=True)

    if design_content is not None:
        (spec_dir / "design.md").write_text(design_content)

    if tasks_content is not None:
        (spec_dir / "tasks.md").write_text(tasks_content)

    if features_content is not None:
        features_dir = spec_dir / "features"
        features_dir.mkdir(exist_ok=True)
        (features_dir / "test.feature").write_text(features_content)


VALID_DESIGN_CONTENT = (
    "# Design Document\n"
    "\n"
    "## Summary\n"
    "A brief summary of the feature.\n"
    "\n"
    "## Approach\n"
    "Implementation approach.\n"
    "\n"
    "## Architecture Decisions\n"
    "Decision 1: Use Python\n"
    "\n"
    "## BDD/TDD Strategy\n"
    "We will use BDD+TDD approach\n"
    "\n"
    "## Code Simplification Constraints\n"
    "Keep it minimal.\n"
    "\n"
    "## BDD Scenario Inventory\n"
    "Scenario 1: Basic flow\n"
    "\n"
    "## Existing Components to Reuse\n"
    "None.\n"
    "\n"
    "## Verification\n"
    "Tests will verify the implementation\n"
)

VALID_TASKS_CONTENT = (
    "# Tasks\n"
    "\n"
    "### Task 1.1: Implement feature\n"
    "Context: Implement the core feature logic.\n"
    "Verification: Run the full test suite.\n"
    "Scenario Coverage: Test scenario in test.feature.\n"
    "Loop Type: TDD-only\n"
    "Behavioral Contract: Must pass all tests.\n"
    "Simplification Focus: Keep implementation minimal.\n"
    "BDD Verification: N/A — TDD-only task.\n"
    "Advanced Test Verification: N/A — no advanced tests planned.\n"
    "Runtime Verification: N/A — no runtime changes.\n"
    "Status: 🟢 DONE\n"
    "- [x] Step 1: Write test\n"
    "- [x] Step 2: Implement\n"
)

VALID_FEATURE_CONTENT = (
    "Feature: Test Feature\n"
    "  Scenario: Test scenario\n"
    "    Given a condition\n"
    "    When action\n"
    "    Then result\n"
)


@pytest.fixture
def valid_spec_dir(tmp_path: Path) -> Path:
    """Create a valid spec directory structure."""
    spec_dir = tmp_path / "specs" / "2026-03-28-test-feature"
    _create_spec_files(
        spec_dir,
        design_content=VALID_DESIGN_CONTENT,
        tasks_content=VALID_TASKS_CONTENT,
        features_content=VALID_FEATURE_CONTENT,
    )
    return spec_dir


@pytest.fixture
def invalid_spec_dir(tmp_path: Path) -> Path:
    """Create an invalid spec directory structure."""
    spec_dir = tmp_path / "specs" / "2026-03-28-invalid-feature"
    _create_spec_files(
        spec_dir,
        design_content="# Design Document\n\n## Some Section\nContent here\n",
        tasks_content="# Tasks\n\nSome tasks here\n",
    )
    return spec_dir


class TestCLI:
    """Tests for CLI interface."""

    def test_help_shows_validate_command(self, runner: CliRunner) -> None:
        """Test that help shows the validate command."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "validate" in result.output

    def test_validate_help_shows_options(self, runner: CliRunner) -> None:
        """Test that validate help shows all options."""
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--plan" in result.output
        assert "--build" in result.output
        assert "--task" in result.output

    def test_validate_requires_mode(self, runner: CliRunner) -> None:
        """Test that validate requires a mode flag."""
        result = runner.invoke(main, ["validate"])
        assert result.exit_code != 0


class TestGetLatestSpecDir:
    """Tests for get_latest_spec_dir function."""

    def test_returns_latest_spec_dir(self, tmp_path: Path) -> None:
        """Test that it returns the latest spec directory by name."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        (specs_dir / "2026-03-01-old-feature").mkdir()
        (specs_dir / "2026-03-28-new-feature").mkdir()

        result = get_latest_spec_dir(specs_dir)
        assert result.name == "2026-03-28-new-feature"

    def test_exits_when_no_specs_dir(self, tmp_path: Path) -> None:
        """Test that it raises SpecNotFoundError when specs directory doesn't exist."""
        specs_dir = tmp_path / "specs"

        with pytest.raises(SpecNotFoundError):
            get_latest_spec_dir(specs_dir)

    def test_exits_when_no_spec_dirs(self, tmp_path: Path) -> None:
        """Test that it raises SpecNotFoundError when specs directory is empty."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        with pytest.raises(SpecNotFoundError):
            get_latest_spec_dir(specs_dir)


class TestValidatePlan:
    """Tests for validate_plan function."""

    def test_valid_spec_passes(self, valid_spec_dir: Path) -> None:
        """Test that a valid spec passes validation."""
        result = validate_plan(valid_spec_dir)
        assert result.is_valid is True

    def test_missing_design_file_fails(self, tmp_path: Path) -> None:
        """Test that missing design.md fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        (spec_dir / "tasks.md").write_text("### Task 1.1: Test\nStatus: TODO\n")

        result = validate_plan(spec_dir)
        assert result.is_valid is False

    def test_missing_tasks_file_fails(self, tmp_path: Path) -> None:
        """Test that missing tasks.md fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        (spec_dir / "design.md").write_text(
            "## Architecture Decisions\n## BDD/TDD Strategy\n## Verification\n"
        )

        result = validate_plan(spec_dir)
        assert result.is_valid is False

    def test_missing_design_section_fails(self, tmp_path: Path) -> None:
        """Test that missing required design section fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        _create_spec_files(
            spec_dir,
            design_content="## Some Section\n",
            tasks_content="### Task 1.1: Test\nStatus: TODO\n",
        )

        result = validate_plan(spec_dir)
        assert result.is_valid is False

    def test_invalid_tasks_structure_fails(self, tmp_path: Path) -> None:
        """Test that invalid tasks.md structure fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        _create_spec_files(
            spec_dir,
            design_content="## Architecture Decisions\n## BDD/TDD Strategy\n## Verification\n",
            tasks_content="# Tasks\nSome content without task definitions\n",
        )

        result = validate_plan(spec_dir)
        assert result.is_valid is False

    def test_duplicate_task_ids_fail(self, tmp_path: Path) -> None:
        """Test that duplicate task IDs violate the task contract."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: First task\n"
            "Context: Build first piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
            "\n"
            "### Task 1.1: Duplicate task\n"
            "Context: Build second piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_tasks_structure(spec_dir)

        assert result.is_valid is False
        assert any("Duplicate task ID" in e.message for e in result.errors)

    def test_task_missing_status_fails_even_when_other_task_has_status(
        self, tmp_path: Path
    ) -> None:
        """Test that Status is required per task, not just somewhere in tasks.md."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Has status\n"
            "Context: Build first piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
            "\n"
            "### Task 1.2: Missing status\n"
            "Context: Build second piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "- [ ] Step 1: Write test\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_tasks_structure(spec_dir)

        assert result.is_valid is False
        assert any(
            e.message == "Task '1.2: Missing status' is missing required field: 'Status:'"
            for e in result.errors
        )

    def test_missing_simplification_focus_fails(self, tmp_path: Path) -> None:
        """Test that tasks must include Simplification Focus field."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Has all fields\n"
            "Context: Build first piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
            "\n"
            "### Task 1.2: Missing simplification focus\n"
            "Context: Build second piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_tasks_structure(spec_dir)

        assert result.is_valid is False
        assert any(
            e.message
            == "Task '1.2: Missing simplification focus' is missing required field: 'Simplification Focus:'"
            for e in result.errors
        )

    def test_missing_bdd_verification_fails(self, tmp_path: Path) -> None:
        """Test that tasks must include BDD Verification field."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Has all fields\n"
            "Context: Build first piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
            "\n"
            "### Task 1.2: Missing BDD verification\n"
            "Context: Build second piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_tasks_structure(spec_dir)

        assert result.is_valid is False
        assert any(
            e.message
            == "Task '1.2: Missing BDD verification' is missing required field: 'BDD Verification:'"
            for e in result.errors
        )

    def test_invalid_task_status_fails(self, tmp_path: Path) -> None:
        """Test that task statuses must use the contract's allowed markers."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Invalid status\n"
            "Context: Build piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: DONE\n"
            "- [ ] Step 1: Write test\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_tasks_structure(spec_dir)

        assert result.is_valid is False
        assert any("invalid Status" in e.message for e in result.errors)

    def test_task_without_checkbox_fails(self, tmp_path: Path) -> None:
        """Test that every task block must include at least one checkbox step."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: No checkbox\n"
            "Context: Build piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔴 TODO\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_tasks_structure(spec_dir)

        assert result.is_valid is False
        assert any("contains no step checkboxes" in e.message for e in result.errors)

    def test_na_required_field_without_reason_fails(self, tmp_path: Path) -> None:
        """Test that N/A placeholders must include a reason."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Bare N/A\n"
            "Context: Build piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A\n"
            "Advanced Test Verification: N/A\n"
            "Runtime Verification: N/A\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_tasks_structure(spec_dir)

        assert result.is_valid is False
        assert any("N/A with a brief reason" in e.message for e in result.errors)

    def test_incomplete_dcr_block_fails(self, tmp_path: Path) -> None:
        """Test that DCR packets must contain all required sections."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Blocked task\n"
            "Context: Build piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: Feature file + scenario.\n"
            "Loop Type: BDD+TDD\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: uv run behave features/example.feature\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔄 DCR\n"
            "- [ ] Step 1: Resolve design issue\n"
            "\n"
            "🔄 Design Change Request — Task 1.1: Blocked task\n"
            "Scenario Coverage: Feature file + scenario.\n"
            "Problem: Current design is infeasible.\n"
            "What We Tried: Ran the failing scenario.\n"
            "Failure Evidence: AssertionError: expected success.\n"
            "Failing Step: When the user submits the form.\n"
            "Suggested Change: Update the design boundary.\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_tasks_structure(spec_dir)

        assert result.is_valid is False
        assert any("Incomplete 🔄 Design Change Request packet" in e.message for e in result.errors)

    def test_incomplete_build_blocked_packet_fails(self, tmp_path: Path) -> None:
        """Test that build-block packets must contain all required sections."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Failed task\n"
            "Context: Build piece.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: Feature file + scenario.\n"
            "Loop Type: BDD+TDD\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: uv run behave features/example.feature\n"
            "Advanced Test Verification: N/A — no advanced tests planned.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔄 DCR\n"
            "- [ ] Step 1: Resolve design issue\n"
            "\n"
            "🛑 Build Blocked — Task 1.1: Failed task\n"
            "Reason: 3 consecutive failed attempts.\n"
            "Loop Type: BDD+TDD\n"
            "Scenario Coverage: Feature file + scenario.\n"
            "What We Tried: Attempted three implementations.\n"
            "Failure Evidence: AssertionError: expected success.\n"
            "Failing Step: When the user submits the form.\n"
            "Suggested Design Change: Update the design boundary.\n"
            "Impact: Task 1.1 remains blocked.\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_tasks_structure(spec_dir)

        assert result.is_valid is False
        assert any("Incomplete 🛑 Build Blocked packet" in e.message for e in result.errors)


class TestValidateBuild:
    """Tests for validate_build function."""

    def test_all_tasks_done_passes(self, tmp_path: Path, monkeypatch) -> None:
        """Test that all tasks marked DONE with checked steps passes."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "### Task 1.1: Test Task\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Complete\n"
            "- [x] Step 2: Complete\n"
        )

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "clean.py").write_text("def foo():\n    return 42\n")

        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)

        _create_spec_files(spec_dir, tasks_content=tasks_content)

        monkeypatch.chdir(tmp_path)
        result = validate_build(spec_dir)
        assert result.is_valid is True

    def test_todo_task_fails(self, tmp_path: Path) -> None:
        """Test that TODO task fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = "### Task 1.1: Test Task\nStatus: 🔴 TODO\n- [ ] Step 1: Not done\n"
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_build(spec_dir)
        assert result.is_valid is False

    def test_in_progress_task_fails(self, tmp_path: Path) -> None:
        """Test that IN PROGRESS task fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "### Task 1.1: Test Task\nStatus: 🟡 IN PROGRESS\n- [ ] Step 1: In progress\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_build(spec_dir)
        assert result.is_valid is False

    def test_dcr_task_fails(self, tmp_path: Path) -> None:
        """Test that DCR task fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = "### Task 1.1: Test Task\nStatus: 🔄 DCR\n- [ ] Step 1: Blocked\n"
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_build(spec_dir)
        assert result.is_valid is False

    def test_unchecked_steps_fails(self, tmp_path: Path) -> None:
        """Test that DONE task with unchecked steps fails validation."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = (
            "### Task 1.1: Test Task\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Complete\n"
            "- [ ] Step 2: Not complete\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        result = validate_build(spec_dir)
        assert result.is_valid is False

    def test_skipped_task_warns(self, tmp_path: Path, monkeypatch) -> None:
        """Test that skipped task warns but passes."""
        spec_dir = tmp_path / "specs" / "test"
        spec_dir.mkdir(parents=True)

        tasks_content = "### Task 1.1: Test Task\nStatus: ⏭️ SKIPPED\n- [ ] Step 1: Skipped\n"
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        monkeypatch.chdir(tmp_path)
        result = validate_build(spec_dir)
        assert result.is_valid is True


class TestValidateTask:
    """Tests for validate_task function."""

    def test_clean_codebase_passes(self, tmp_path: Path, monkeypatch) -> None:
        """Test that clean codebase passes validation."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "clean.py").write_text("def foo():\n    return 42\n")

        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)

        monkeypatch.chdir(tmp_path)
        result = validate_task()
        assert result.is_valid is True

    def test_codebase_with_todos_fails(self, tmp_path: Path, monkeypatch) -> None:
        """Test that codebase with TODOs fails validation."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        dirty_file = src_dir / "dirty.py"
        dirty_file.write_text("# TODO: fix this\n")

        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
        clean_file = src_dir / "clean.py"
        clean_file.write_text("pass\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "--no-gpg-sign", "-m", "init"], cwd=tmp_path, capture_output=True
        )
        monkeypatch.setattr(
            "pb_spec.validation.build.get_git_modified_files",
            lambda _root_dir=".": {dirty_file},
        )

        monkeypatch.chdir(tmp_path)
        result = validate_task()
        assert result.is_valid is False
        assert len(result.errors) > 0


class TestValidateCommand:
    """Tests for validate command integration."""

    def test_task_mode_passes_on_clean_code(self, runner: CliRunner) -> None:
        """Test that --task mode passes on clean codebase."""
        with runner.isolated_filesystem():
            with open("clean.py", "w") as f:
                f.write("def foo():\n    return 42\n")

            result = runner.invoke(main, ["validate", "--task"])
            assert result.exit_code == 0
            assert "passed" in result.output.lower() or "✅" in result.output


CONSOLIDATED_VALID_DESIGN = (
    "# Design: Codebase Quality Improvements\n"
    "\n"
    "## Summary\n"
    "Consolidated improvements across correctness, security, and performance.\n"
    "\n"
    "## Approach\n"
    "Implement findings sequentially.\n"
    "\n"
    "## Findings\n"
    "\n"
    "### Finding 1: Fix N+1 query\n"
    "- **Category:** performance\n"
    "- **Impact:** HIGH\n"
    "\n"
    "#### Approach\n"
    "Add batch loading.\n"
    "\n"
    "## Architecture Decisions\n"
    "### AD-01: Use batch loading\n"
    "- **Status:** Accepted\n"
    "\n"
    "**Context:** N+1 queries detected.\n"
    "**Decision:** Use DataLoader pattern.\n"
    "**Consequences:** Reduces query count.\n"
    "\n"
    "## BDD/TDD Strategy\n"
    "BDD+TDD with behave.\n"
    "\n"
    "## Code Simplification Constraints\n"
    "Keep minimal.\n"
    "\n"
    "## BDD Scenario Inventory\n"
    "- features/performance.feature — Batch loading → Task 1.1\n"
    "\n"
    "## Existing Components to Reuse\n"
    "None.\n"
    "\n"
    "## Verification\n"
    "Run full test suite.\n"
)

CONSOLIDATED_VALID_TASKS = (
    "# Tasks\n"
    "\n"
    "### Task 1.1: Fix N+1 query\n"
    "Context: Address performance issue.\n"
    "Verification: Run tests.\n"
    "Scenario Coverage: features/performance.feature — Batch loading.\n"
    "Loop Type: BDD+TDD\n"
    "Behavioral Contract: Preserve existing behavior.\n"
    "Simplification Focus: Reduce nesting.\n"
    "BDD Verification: uv run behave features/performance.feature\n"
    "Advanced Test Verification: N/A — no advanced tests planned.\n"
    "Runtime Verification: N/A — no runtime changes.\n"
    "Status: 🔴 TODO\n"
    "- [ ] Step 1: Write failing test\n"
)

CONSOLIDATED_CROSS_FINDING_TASKS = (
    "# Tasks\n"
    "\n"
    "### Task 1.1: Finding 1 — Fix bug\n"
    "Context: Fix the bug.\n"
    "Verification: Run tests.\n"
    "Scenario Coverage: features/correctness.feature — Bug fix.\n"
    "Loop Type: BDD+TDD\n"
    "Behavioral Contract: Must pass.\n"
    "Simplification Focus: Keep minimal.\n"
    "BDD Verification: uv run behave features/correctness.feature\n"
    "Advanced Test Verification: N/A — no advanced tests.\n"
    "Runtime Verification: N/A — no runtime changes.\n"
    "Status: 🔴 TODO\n"
    "- [ ] Step 1: Write test\n"
    "\n"
    "### Task 2.1: Finding 2 — Add feature\n"
    "Context: Add new feature.\n"
    "Verification: Run tests.\n"
    "Scenario Coverage: features/security.feature — Auth check.\n"
    "Loop Type: BDD+TDD\n"
    "Behavioral Contract: Must pass.\n"
    "Simplification Focus: Keep minimal.\n"
    "BDD Verification: uv run behave features/security.feature\n"
    "Advanced Test Verification: N/A — no advanced tests.\n"
    "Runtime Verification: N/A — no runtime changes.\n"
    "Status: 🔴 TODO\n"
    "- [ ] Step 1: Write test\n"
)

FULL_MODE_DESIGN = (
    "# Design: Full Feature\n"
    "\n"
    "## Executive Summary\n"
    "Complete feature implementation.\n"
    "\n"
    "## Requirements & Goals\n"
    "- **[REQ-01]:** The system *shall* validate inputs.\n"
    "\n"
    "## Architecture Overview\n"
    "```mermaid\n"
    "graph TD\n"
    "  A[Client] --> B[Server]\n"
    "```\n"
    "\n"
    "## Architecture Decisions\n"
    "### AD-01: Use REST API\n"
    "- **Status:** Accepted\n"
    "\n"
    "**Context:** Need external API.\n"
    "**Decision:** Use REST.\n"
    "**Consequences:** Simple integration.\n"
    "\n"
    "## Data Models\n"
    "```dbml\n"
    "Table users {\n"
    "  id integer [pk]\n"
    "  name varchar\n"
    "}\n"
    "```\n"
    "\n"
    "## Interface Contracts\n"
    "```python\n"
    "class UserProto(Protocol):\n"
    "    def get_name(self) -> str: ...\n"
    "```\n"
    "\n"
    "## Detailed Design\n"
    "Implementation details.\n"
    "\n"
    "## Verification & Testing Strategy\n"
    "BDD + unit tests.\n"
    "\n"
    "## Implementation Plan\n"
    "- [ ] Phase 1: Core\n"
)


class TestConsolidatedSpec:
    """Tests for consolidated spec format (pb-improve → pb-build flow)."""

    def test_consolidated_design_passes_lightweight(self, tmp_path: Path) -> None:
        """Test that consolidated design.md with Findings section passes lightweight validation."""
        spec_dir = tmp_path / "specs" / "2026-06-12-improvements"
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=CONSOLIDATED_VALID_TASKS,
            features_content="Feature: Performance\n  Scenario: Batch loading\n    Given orders\n    When fetched\n    Then one query\n",
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is True

    def test_consolidated_tasks_with_cross_finding_numbering(self, tmp_path: Path) -> None:
        """Test that tasks numbered across findings (1.1, 2.1) pass validation."""
        spec_dir = tmp_path / "specs" / "2026-06-12-multi-finding"
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=CONSOLIDATED_CROSS_FINDING_TASKS,
            features_content=(
                "Feature: Correctness\n  Scenario: Bug fix\n    Given bug\n    When fixed\n    Then works\n"
                "Feature: Security\n  Scenario: Auth\n    Given user\n    When auth\n    Then ok\n"
            ),
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is True

    def test_consolidated_design_missing_approach_fails(self, tmp_path: Path) -> None:
        """Test that consolidated design.md missing Approach section fails."""
        spec_dir = tmp_path / "specs" / "2026-06-12-no-approach"
        design_content = (
            "# Design: Improvements\n"
            "\n"
            "## Summary\n"
            "Summary.\n"
            "\n"
            "## Architecture Decisions\n"
            "Decision.\n"
            "\n"
            "## BDD/TDD Strategy\n"
            "Strategy.\n"
            "\n"
            "## Code Simplification Constraints\n"
            "Keep minimal.\n"
            "\n"
            "## BDD Scenario Inventory\n"
            "Scenarios.\n"
            "\n"
            "## Existing Components to Reuse\n"
            "None.\n"
            "\n"
            "## Verification\n"
            "Run tests.\n"
        )
        _create_spec_files(
            spec_dir,
            design_content=design_content,
            tasks_content=CONSOLIDATED_VALID_TASKS,
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Approach" in e.message for e in result.errors)

    def test_consolidated_tasks_missing_loop_type_fails(self, tmp_path: Path) -> None:
        """Test that consolidated tasks.md missing Loop Type field fails."""
        spec_dir = tmp_path / "specs" / "2026-06-12-no-loop-type"
        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Fix bug\n"
            "Context: Fix it.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
        )
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=tasks_content,
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Loop Type" in e.message for e in result.errors)

    def test_consolidated_tasks_missing_status_fails(self, tmp_path: Path) -> None:
        """Test that consolidated tasks.md missing Status field fails."""
        spec_dir = tmp_path / "specs" / "2026-06-12-no-status"
        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Fix bug\n"
            "Context: Fix it.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: N/A — internal task.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "BDD Verification: N/A — TDD-only task.\n"
            "Advanced Test Verification: N/A — no advanced tests.\n"
            "Runtime Verification: N/A — no runtime changes.\n"
            "- [ ] Step 1: Write test\n"
        )
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=tasks_content,
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Status" in e.message for e in result.errors)

    def test_consolidated_build_passes_when_all_done(self, tmp_path: Path, monkeypatch) -> None:
        """Test that consolidated spec passes build validation when all tasks are DONE."""
        spec_dir = tmp_path / "specs" / "2026-06-12-done"
        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Fix bug\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Write test\n"
            "- [x] Step 2: Implement\n"
            "\n"
            "### Task 2.1: Add feature\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Write test\n"
            "- [x] Step 2: Implement\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "clean.py").write_text("def foo():\n    return 42\n")

        import subprocess

        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)

        monkeypatch.chdir(tmp_path)
        result = validate_build(spec_dir)
        assert result.is_valid is True

    def test_consolidated_build_fails_when_first_task_todo(self, tmp_path: Path) -> None:
        """Test that consolidated spec fails build when first task is TODO."""
        spec_dir = tmp_path / "specs" / "2026-06-12-partial"
        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Fix bug\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
            "\n"
            "### Task 2.1: Add feature\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1: Complete\n"
        )
        _create_spec_files(spec_dir, tasks_content=tasks_content)
        result = validate_build(spec_dir)
        assert result.is_valid is False


class TestFullModeSpec:
    """Tests for full-mode spec format (pb-plan → pb-build flow)."""

    def test_full_mode_design_passes(self, tmp_path: Path) -> None:
        """Test that full-mode design.md with all required sections passes."""
        spec_dir = tmp_path / "specs" / "2026-06-12-full-mode"
        _create_spec_files(
            spec_dir,
            design_content=FULL_MODE_DESIGN,
            tasks_content=CONSOLIDATED_VALID_TASKS,
            features_content="Feature: Test\n  Scenario: Test\n    Given a\n    When b\n    Then c\n",
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is True

    def test_full_mode_missing_architecture_decisions_fails(self, tmp_path: Path) -> None:
        """Test that full-mode design.md missing Architecture Decisions fails."""
        spec_dir = tmp_path / "specs" / "2026-06-12-no-ad"
        design_content = (
            "# Design: Full Feature\n"
            "\n"
            "## Executive Summary\n"
            "Summary.\n"
            "\n"
            "## Requirements & Goals\n"
            "- **[REQ-01]:** The system *shall* validate.\n"
            "\n"
            "## Architecture Overview\n"
            "```mermaid\ngraph TD\n  A-->B\n```\n"
            "\n"
            "## Data Models\n"
            "```dbml\nTable t { id integer [pk] }\n```\n"
            "\n"
            "## Interface Contracts\n"
            "```python\nproto...\n```\n"
            "\n"
            "## Detailed Design\n"
            "Details.\n"
            "\n"
            "## Verification & Testing Strategy\n"
            "Strategy.\n"
            "\n"
            "## Implementation Plan\n"
            "- [ ] Phase 1\n"
        )
        _create_spec_files(
            spec_dir,
            design_content=design_content,
            tasks_content=CONSOLIDATED_VALID_TASKS,
            features_content="Feature: Test\n  Scenario: Test\n    Given a\n    When b\n    Then c\n",
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Architecture Decisions" in e.message for e in result.errors)

    def test_full_mode_missing_data_models_fails(self, tmp_path: Path) -> None:
        """Test that full-mode design.md missing Data Models fails."""
        spec_dir = tmp_path / "specs" / "2026-06-12-no-dm"
        design_content = (
            "# Design: Full Feature\n"
            "\n"
            "## Executive Summary\n"
            "Summary.\n"
            "\n"
            "## Requirements & Goals\n"
            "- **[REQ-01]:** The system *shall* validate.\n"
            "\n"
            "## Architecture Overview\n"
            "```mermaid\ngraph TD\n  A-->B\n```\n"
            "\n"
            "## Architecture Decisions\n"
            "### AD-01: Decision\n"
            "- **Status:** Accepted\n"
            "\n"
            "**Context:** C\n**Decision:** D\n**Consequences:** E\n"
            "\n"
            "## Interface Contracts\n"
            "```python\nproto...\n```\n"
            "\n"
            "## Detailed Design\n"
            "Details.\n"
            "\n"
            "## Verification & Testing Strategy\n"
            "Strategy.\n"
            "\n"
            "## Implementation Plan\n"
            "- [ ] Phase 1\n"
        )
        _create_spec_files(
            spec_dir,
            design_content=design_content,
            tasks_content=CONSOLIDATED_VALID_TASKS,
            features_content="Feature: Test\n  Scenario: Test\n    Given a\n    When b\n    Then c\n",
        )
        result = validate_plan(spec_dir)
        assert result.is_valid is False
        assert any("Data Models" in e.message for e in result.errors)


class TestTaskMissingFields:
    """Tests for tasks.md missing required fields (pb-improve → pb-build contract)."""

    def test_missing_simplification_focus_fails(self, tmp_path: Path) -> None:
        """Test that task missing Simplification Focus field fails validation."""
        spec_dir = tmp_path / "specs" / "2026-06-13-missing-sf"
        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Fix bug\n"
            "Context: Fix the bug.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: features/correctness.feature — Bug fix.\n"
            "Loop Type: BDD+TDD\n"
            "Behavioral Contract: Must pass.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
            "- [ ] BDD Verification: run behave\n"
            "- [ ] Advanced Test Verification: N/A — no advanced tests.\n"
            "- [ ] Runtime Verification: N/A — no runtime changes.\n"
        )
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=tasks_content,
            features_content="Feature: Test\n  Scenario: Test\n    Given a\n    When b\n    Then c\n",
        )
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any(
            "Simplification Focus" in e.message and "missing required field" in e.message
            for e in result.errors
        )

    def test_missing_bdd_verification_fails(self, tmp_path: Path) -> None:
        """Test that task missing BDD Verification field fails validation."""
        spec_dir = tmp_path / "specs" / "2026-06-13-missing-bddv"
        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Fix bug\n"
            "Context: Fix the bug.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: features/correctness.feature — Bug fix.\n"
            "Loop Type: BDD+TDD\n"
            "Behavioral Contract: Must pass.\n"
            "Simplification Focus: Keep minimal.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
            "- [ ] Advanced Test Verification: N/A — no advanced tests.\n"
            "- [ ] Runtime Verification: N/A — no runtime changes.\n"
        )
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=tasks_content,
            features_content="Feature: Test\n  Scenario: Test\n    Given a\n    When b\n    Then c\n",
        )
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        assert any(
            "BDD Verification" in e.message and "missing required field" in e.message
            for e in result.errors
        )

    def test_missing_both_simplification_and_bdd_verification_fails(self, tmp_path: Path) -> None:
        """Test that task missing both Simplification Focus and BDD Verification fails."""
        spec_dir = tmp_path / "specs" / "2026-06-13-missing-both"
        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: Fix bug\n"
            "Context: Fix the bug.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: features/correctness.feature — Bug fix.\n"
            "Loop Type: BDD+TDD\n"
            "Behavioral Contract: Must pass.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
            "- [ ] Advanced Test Verification: N/A — no advanced tests.\n"
            "- [ ] Runtime Verification: N/A — no runtime changes.\n"
        )
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=tasks_content,
            features_content="Feature: Test\n  Scenario: Test\n    Given a\n    When b\n    Then c\n",
        )
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        sf_missing = any(
            "Simplification Focus" in e.message and "missing required field" in e.message
            for e in result.errors
        )
        bddv_missing = any(
            "BDD Verification" in e.message and "missing required field" in e.message
            for e in result.errors
        )
        assert sf_missing, "Expected Simplification Focus missing error"
        assert bddv_missing, "Expected BDD Verification missing error"

    def test_multiple_tasks_missing_fields_reports_all(self, tmp_path: Path) -> None:
        """Test that validation reports missing fields for ALL tasks, not just the first."""
        spec_dir = tmp_path / "specs" / "2026-06-13-multi-missing"
        tasks_content = (
            "# Tasks\n"
            "\n"
            "### Task 1.1: First task\n"
            "Context: First.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: features/test.feature — Scenario.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
            "\n"
            "### Task 1.2: Second task\n"
            "Context: Second.\n"
            "Verification: Run tests.\n"
            "Scenario Coverage: features/test.feature — Scenario.\n"
            "Loop Type: TDD-only\n"
            "Behavioral Contract: Must pass.\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1: Write test\n"
        )
        _create_spec_files(
            spec_dir,
            design_content=CONSOLIDATED_VALID_DESIGN,
            tasks_content=tasks_content,
            features_content="Feature: Test\n  Scenario: Test\n    Given a\n    When b\n    Then c\n",
        )
        result = validate_tasks_structure(spec_dir)
        assert result.is_valid is False
        # Both tasks should report missing Simplification Focus
        sf_errors = [e for e in result.errors if "Simplification Focus" in e.message]
        assert len(sf_errors) == 2, f"Expected 2 Simplification Focus errors, got {len(sf_errors)}"
