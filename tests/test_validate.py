"""Unit tests for the validate command."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from pb_spec.cli import main
from pb_spec.commands.discovery import get_latest_spec_dir
from pb_spec.exceptions import SpecNotFoundError
from pb_spec.validation import validate_build, validate_plan, validate_task
from pb_spec.validation.plan import validate_tasks_structure


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
            lambda: {dirty_file},
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
